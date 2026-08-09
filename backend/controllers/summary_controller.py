from flask import request, jsonify, g
from backend.controllers._helpers import require_json_body
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import paper_model, chunk_model
from backend.services import groq_service
from backend.config import settings


def _batch_chunks(chunks: list[dict], budget: int) -> list[list[dict]]:
    """Split chunks into batches that each fit under the LLM input budget.

    Each batch's joined text (plus a per-batch header allowance) stays
    within ``budget`` so a full-paper summary is produced from every part
    of the paper, not just the beginning.
    """
    header_allowance = 500
    batches = []
    current: list[dict] = []
    current_len = 0
    for chunk in chunks:
        text = chunk.get("chunk_text", "")
        if not text:
            continue
        chunk_len = len(text)
        if current and current_len + chunk_len + header_allowance > budget:
            batches.append(current)
            current = []
            current_len = 0
        current.append(chunk)
        current_len += chunk_len
    if current:
        batches.append(current)
    return batches


def handle_summarize():
    body = require_json_body()

    paper_id = (body.get("paper_id") or "").strip()
    if not paper_id:
        raise AppError(
            message="Field 'paper_id' is required.",
            status_code=400,
            code="MISSING_PAPER_ID",
        )

    if not ObjectId.is_valid(paper_id):
        raise AppError(
            message=f"Invalid paper ID format: '{paper_id}'.",
            status_code=400,
            code="INVALID_ID",
        )

    force = body.get("force_regenerate", False)

    user_id = getattr(g, "user_id", None)
    paper = paper_model.get_paper(paper_id, user_id=user_id)
    if not paper:
        raise AppError(
            message=f"No paper found with ID '{paper_id}'.",
            status_code=404,
            code="PAPER_NOT_FOUND",
        )

    if not force and paper.get("summary"):
        return jsonify({
            "success": True,
            "data": {
                "summary": paper["summary"],
                "cached": True,
            },
        }), 200

    if paper.get("status") != "processed":
        raise AppError(
            message=f"Paper '{paper_id}' is not yet fully processed. Current status: {paper.get('status', 'unknown')}.",
            status_code=422,
            code="PAPER_NOT_PROCESSED",
        )

    chunks = chunk_model.get_chunks_by_paper(paper_id)
    if not chunks:
        raise AppError(
            message=f"No text content found for paper '{paper_id}'. The paper may be empty or scanned.",
            status_code=422,
            code="NO_CONTENT",
        )

    batches = _batch_chunks(chunks, settings.MAX_LLM_INPUT_CHARS)
    if len(batches) == 1:
        context = "\n\n".join(c["chunk_text"] for c in batches[0])
        summary = groq_service.generate_summary(context)
    else:
        partials = []
        for batch in batches:
            context = "\n\n".join(c["chunk_text"] for c in batch)
            partials.append(groq_service.generate_summary(context))
        summary = groq_service.merge_summaries(partials)
    paper_model.update_paper(paper_id, {"summary": summary})

    return jsonify({
        "success": True,
        "data": {
            "summary": summary,
            "cached": False,
        },
    }), 200
