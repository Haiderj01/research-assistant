from unittest.mock import patch, MagicMock
import pytest
from backend.services import gap_analysis_service
from backend.middlewares.error_handler import AppError


@pytest.fixture(autouse=True)
def mock_deps():
    with (
        patch("backend.services.gap_analysis_service.paper_model") as mock_paper,
        patch("backend.services.gap_analysis_service.chunk_model") as mock_chunks,
        patch("backend.services.gap_analysis_service.embedding_service") as mock_embed,
        patch("backend.services.gap_analysis_service.groq_service") as mock_groq,
        patch("backend.services.gap_analysis_service.vector_store") as mock_vs,
    ):
        mock_embed.generate_embedding.return_value = [0.1] * 384
        mock_groq.extract_paper_gaps.return_value = "Limitations: None. Future Work: None."
        mock_groq.synthesize_research_gaps.return_value = (
            "Gap 1:\n"
            "Gap: Model generalization is limited.\n"
            "Supporting Papers: 507f1f77bcf86cd799439011, 507f1f77bcf86cd799439012\n"
            "Strength: multiple\n"
            "Suggested Direction: Evaluate on heterogeneous domains.\n"
        )
        mock_vs.search.return_value = [
            {"chunk_id": "chunk_1", "score": 0.9, "position": 0},
        ]
        mock_chunks.get_chunks_by_vector_ids.return_value = [
            {"vector_id": "chunk_1", "chunk_text": "Limitations of this study..."},
        ]

        def get_paper_side_effect(pid, user_id=None):
            return {
                "_id": pid,
                "title": f"Paper {pid[-4:]}",
                "status": "processed",
            }

        mock_paper.get_paper.side_effect = get_paper_side_effect

        yield {
            "paper": mock_paper,
            "chunks": mock_chunks,
            "embed": mock_embed,
            "groq": mock_groq,
            "vector_store": mock_vs,
        }


VALID_IDS = [
    "507f1f77bcf86cd799439011",
    "507f1f77bcf86cd799439012",
]


class TestGapAnalysisService:
    def test_map_step_called_once_per_paper(self, mock_deps):
        mock_deps["groq"].extract_paper_gaps.side_effect = [
            "Summary A.",
            "Summary B.",
        ]
        result = gap_analysis_service.analyze_research_gaps(VALID_IDS, "user_1")

        assert mock_deps["groq"].extract_paper_gaps.call_count == 2
        assert mock_deps["vector_store"].search.call_count == 2
        assert len(result["per_paper_summaries"]) == 2

    def test_reduce_receives_all_per_paper_summaries(self, mock_deps):
        mock_deps["groq"].extract_paper_gaps.side_effect = [
            "Limitations of A.",
            "Limitations of B.",
        ]
        result = gap_analysis_service.analyze_research_gaps(VALID_IDS, "user_1")

        args, _ = mock_deps["groq"].synthesize_research_gaps.call_args
        summaries_blob = args[0]
        assert "Limitations of A." in summaries_blob
        assert "Limitations of B." in summaries_blob
        assert "507f1f77bcf86cd799439011" in summaries_blob
        assert "507f1f77bcf86cd799439012" in summaries_blob
        assert len(result["gaps"]) == 1
        assert result["gaps"][0]["strength"] == "multiple"
        assert result["gaps"][0]["supporting_papers"] == VALID_IDS

    def test_search_scoped_to_each_paper(self, mock_deps):
        gap_analysis_service.analyze_research_gaps(VALID_IDS, "user_1")

        calls = mock_deps["vector_store"].search.call_args_list
        for call, pid in zip(calls, VALID_IDS):
            kwargs = call.kwargs
            assert kwargs["paper_ids"] == [pid]

    def test_too_few_papers_raises_400(self, mock_deps):
        with pytest.raises(AppError) as exc:
            gap_analysis_service.analyze_research_gaps(
                ["507f1f77bcf86cd799439011"], "user_1"
            )
        assert exc.value.status_code == 400
        assert exc.value.code == "INSUFFICIENT_PAPERS"

    def test_too_many_papers_raises_400(self, mock_deps):
        many = [f"{i:0>24}" for i in range(13)]
        with pytest.raises(AppError) as exc:
            gap_analysis_service.analyze_research_gaps(many, "user_1")
        assert exc.value.status_code == 400
        assert exc.value.code == "TOO_MANY_PAPERS"

    def test_missing_paper_ids_raises_400(self, mock_deps):
        with pytest.raises(AppError) as exc:
            gap_analysis_service.analyze_research_gaps([], "user_1")
        assert exc.value.status_code == 400
        assert exc.value.code == "MISSING_PAPER_IDS"

    def test_invalid_id_format_raises_400(self, mock_deps):
        with pytest.raises(AppError) as exc:
            gap_analysis_service.analyze_research_gaps(
                ["not-an-id", "507f1f77bcf86cd799439011"], "user_1"
            )
        assert exc.value.status_code == 400
        assert exc.value.code == "INVALID_IDS"

    def test_missing_paper_raises_404(self, mock_deps):
        mock_deps["paper"].get_paper.side_effect = lambda pid, user_id=None: None
        with pytest.raises(AppError) as exc:
            gap_analysis_service.analyze_research_gaps(VALID_IDS, "user_1")
        assert exc.value.status_code == 404
        assert exc.value.code == "PAPER_NOT_FOUND"

    def test_unprocessed_paper_raises_422(self, mock_deps):
        def get_paper_side_effect(pid, user_id=None):
            return {"_id": pid, "title": "X", "status": "pending"}

        mock_deps["paper"].get_paper.side_effect = get_paper_side_effect
        with pytest.raises(AppError) as exc:
            gap_analysis_service.analyze_research_gaps(VALID_IDS, "user_1")
        assert exc.value.status_code == 422
        assert exc.value.code == "PAPER_NOT_PROCESSED"

    def test_groq_map_failure_propagates(self, mock_deps):
        mock_deps["groq"].extract_paper_gaps.side_effect = AppError(
            message="boom", status_code=502, code="GROQ_ERROR"
        )
        with pytest.raises(AppError) as exc:
            gap_analysis_service.analyze_research_gaps(VALID_IDS, "user_1")
        assert exc.value.status_code == 502
        assert exc.value.code == "GROQ_ERROR"

    def test_gap_without_supporting_papers_is_dropped(self, mock_deps):
        mock_deps["groq"].synthesize_research_gaps.return_value = (
            "Gap 1:\n"
            "Gap: Ungrounded gap.\n"
            "Supporting Papers: unknown\n"
            "Strength: single\n"
            "Suggested Direction: Explore it.\n"
        )
        result = gap_analysis_service.analyze_research_gaps(VALID_IDS, "user_1")
        assert result["gaps"] == []
