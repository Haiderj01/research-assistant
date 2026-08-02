from flask import request, jsonify, g
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import paper_model, chunk_model
from backend.services import gemini_service


def handle_summarize():
    body = request.get_json(silent=True)
    if body is None:
        raise AppError(
            message="Request body must be valid JSON.",
            status_code=400,
            code="INVALID_JSON",
        )

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

    context = "\n\n".join(c["chunk_text"] for c in chunks)

    summary = gemini_service.generate_summary(context)
    paper_model.update_paper(paper_id, {"summary": summary})

    return jsonify({
        "success": True,
        "data": {
            "summary": summary,
            "cached": False,
        },
    }), 200
