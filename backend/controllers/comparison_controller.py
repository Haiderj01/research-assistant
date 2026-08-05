from flask import request, jsonify, g
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import paper_model, chunk_model
from backend.services import groq_service
from backend.config.settings import settings


def _paper_context_budget(num_papers: int) -> int:
    """Per-paper char budget so all papers fit under the LLM input cap.

    Reserves a fixed allowance for the prompt template and header text,
    then splits the remaining input budget evenly across the papers.
    """
    template_allowance = 2000
    return max(1, (settings.MAX_LLM_INPUT_CHARS - template_allowance) // num_papers)


def _truncate_text(text: str, limit: int) -> str:
    return text[:limit] if len(text) > limit else text


def handle_compare():
    body = request.get_json(silent=True)
    if body is None:
        raise AppError(
            message="Request body must be valid JSON.",
            status_code=400,
            code="INVALID_JSON",
        )

    paper_ids = body.get("paper_ids", [])
    dimensions = body.get("dimensions")

    if not paper_ids or not isinstance(paper_ids, list) or len(paper_ids) < 2:
        raise AppError(
            message="At least two paper IDs are required for comparison.",
            status_code=400,
            code="INSUFFICIENT_PAPERS",
        )

    invalid_ids = [pid for pid in paper_ids if not ObjectId.is_valid(pid)]
    if invalid_ids:
        raise AppError(
            message=f"Invalid paper ID format: {invalid_ids}.",
            status_code=400,
            code="INVALID_IDS",
        )

    if dimensions is not None:
        if not isinstance(dimensions, list) or not dimensions:
            raise AppError(
                message="If provided, 'dimensions' must be a non-empty array of strings.",
                status_code=400,
                code="INVALID_DIMENSIONS",
            )

    user_id = getattr(g, "user_id", None)

    papers = []
    for pid in paper_ids:
        paper = paper_model.get_paper(pid, user_id=user_id)
        if not paper:
            raise AppError(
                message=f"No paper found with ID '{pid}'.",
                status_code=404,
                code="PAPER_NOT_FOUND",
            )
        if paper.get("status") != "processed":
            raise AppError(
                message=f"Paper '{pid}' is not yet fully processed. Current status: {paper.get('status', 'unknown')}.",
                status_code=422,
                code="PAPER_NOT_PROCESSED",
            )
        papers.append(paper)

    all_context_parts = []
    budget = _paper_context_budget(len(papers))
    for paper in papers:
        chunks = chunk_model.get_chunks_by_paper(str(paper["_id"]))
        text = "\n\n".join(c["chunk_text"] for c in chunks) if chunks else ""
        all_context_parts.append(
            f"--- Paper: {paper['title']} ---\n{_truncate_text(text, budget)}"
        )

    context = "\n\n".join(all_context_parts)

    comparison_text = groq_service.generate_comparison(
        context=context,
        dimensions=dimensions or [],
    )

    return jsonify({
        "success": True,
        "data": {
            "paper_ids": paper_ids,
            "comparison": comparison_text,
        },
    }), 200
