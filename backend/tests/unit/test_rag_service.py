from unittest.mock import patch, MagicMock
import pytest
from backend.services.rag_service import answer_query
from backend.middlewares.error_handler import AppError


@pytest.fixture(autouse=True)
def mock_deps():
    with (
        patch("backend.services.rag_service.embedding_service") as mock_embed,
        patch("backend.services.rag_service.groq_service") as mock_groq,
        patch("backend.services.rag_service.chunk_model") as mock_chunks,
        patch("backend.services.rag_service.conversation_model") as mock_conv,
        patch("backend.services.rag_service.question_model") as mock_q,
        patch("backend.services.rag_service.search_history_model") as mock_sh,
        patch("backend.services.rag_service.vector_store") as mock_vs,
    ):
        mock_embed.generate_embedding.return_value = [0.1] * 384
        mock_groq.answer_question.return_value = "This is the generated answer."
        mock_conv.create_conversation.return_value = {"_id": "conv_123"}
        mock_conv.update_conversation.return_value = True
        mock_chunks.get_chunks_by_vector_ids.return_value = [
            {"_id": "oid_1", "vector_id": "chunk_1", "chunk_text": "Paper content about machine learning.",
             "paper_id": "paper_1", "page_number": 1},
            {"_id": "oid_2", "vector_id": "chunk_2", "chunk_text": "More paper content here.",
             "paper_id": "paper_1", "page_number": 2},
        ]
        mock_vs.search.return_value = [
            {"chunk_id": "chunk_1", "score": 0.95, "position": 0},
            {"chunk_id": "chunk_2", "score": 0.80, "position": 1},
        ]

        yield {
            "embed": mock_embed,
            "groq": mock_groq,
            "chunks": mock_chunks,
            "conv": mock_conv,
            "questions": mock_q,
            "search_history": mock_sh,
            "vector_store": mock_vs,
        }


class TestAnswerQuery:
    def test_returns_answer_with_sources(self, mock_deps):
        result = answer_query(
            question="What is this paper about?",
            paper_ids=["paper_1"],
        )
        assert result["answer"] == "This is the generated answer."
        assert len(result["sources"]) == 2
        assert result["conversation_id"] == "conv_123"
        assert result["sources"][0]["chunk_id"] == "chunk_1"

    def test_no_results_returns_fallback_message(self, mock_deps):
        mock_deps["vector_store"].search.return_value = []
        result = answer_query(
            question="Unknown topic?",
            paper_ids=["paper_1"],
        )
        assert "do not contain information" in result["answer"]
        assert result["sources"] == []

    def test_no_matching_chunks_returns_fallback(self, mock_deps):
        mock_deps["vector_store"].search.return_value = [
            {"chunk_id": "nonexistent", "score": 0.5, "position": 0},
        ]
        mock_deps["chunks"].get_chunks_by_vector_ids.return_value = []
        result = answer_query(
            question="Any content?",
            paper_ids=["paper_1"],
        )
        assert "No relevant content" in result["answer"]

    def test_raises_error_for_empty_question(self, mock_deps):
        with pytest.raises(AppError, match="cannot be empty"):
            answer_query(question="", paper_ids=["paper_1"])

    def test_raises_error_for_no_paper_ids(self, mock_deps):
        with pytest.raises(AppError, match="At least one paper"):
            answer_query(question="test?", paper_ids=[])

    def test_paper_scope_filters_cross_paper_chunks(self, mock_deps):
        mock_deps["chunks"].get_chunks_by_vector_ids.return_value = [
            {"_id": "oid_1", "vector_id": "chunk_1", "chunk_text": "Paper A content.",
             "paper_id": "paper_a", "page_number": 1},
            {"_id": "oid_2", "vector_id": "chunk_2", "chunk_text": "Paper B content.",
             "paper_id": "paper_b", "page_number": 1},
            {"_id": "oid_3", "vector_id": "chunk_3", "chunk_text": "Paper A more content.",
             "paper_id": "paper_a", "page_number": 2},
        ]
        mock_deps["vector_store"].search.return_value = [
            {"chunk_id": "chunk_1", "score": 0.95, "position": 0},
            {"chunk_id": "chunk_2", "score": 0.90, "position": 1},
            {"chunk_id": "chunk_3", "score": 0.85, "position": 2},
        ]

        result = answer_query(
            question="Test?",
            paper_ids=["paper_a"],
        )
        assert len(result["sources"]) == 2
        for s in result["sources"]:
            assert s["paper_id"] == "paper_a"
        assert "Paper B" not in str(result["sources"])

    def test_paper_ids_passed_to_vector_search(self, mock_deps):
        mock_deps["vector_store"].search.return_value = [
            {"chunk_id": "chunk_1", "score": 0.95, "position": 0},
        ]
        mock_deps["chunks"].get_chunks_by_vector_ids.return_value = [
            {"_id": "oid_1", "vector_id": "chunk_1", "chunk_text": "Content.",
             "paper_id": "paper_a", "page_number": 1},
        ]

        answer_query(
            question="Test?",
            paper_ids=["paper_a", "paper_b"],
        )

        mock_deps["vector_store"].search.assert_called_once()
        _, kwargs = mock_deps["vector_store"].search.call_args
        assert kwargs["paper_ids"] == ["paper_a", "paper_b"]

    def test_scoped_query_never_returns_other_paper_chunks(self, mock_deps):
        mock_deps["chunks"].get_chunks_by_vector_ids.return_value = [
            {"_id": "oid_1", "vector_id": "chunk_1", "chunk_text": "Paper A content.",
             "paper_id": "paper_a", "page_number": 1},
            {"_id": "oid_2", "vector_id": "chunk_2", "chunk_text": "Paper B content.",
             "paper_id": "paper_b", "page_number": 1},
        ]
        mock_deps["vector_store"].search.return_value = [
            {"chunk_id": "chunk_1", "score": 0.95, "position": 0},
            {"chunk_id": "chunk_2", "score": 0.90, "position": 1},
        ]

        result = answer_query(
            question="Test?",
            paper_ids=["paper_a"],
        )
        for s in result["sources"]:
            assert s["paper_id"] != "paper_b"
