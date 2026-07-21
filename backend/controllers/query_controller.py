from flask import request, jsonify
from backend.middlewares.error_handler import AppError
from backend.services import rag_service


def handle_ask():
    body = request.get_json(silent=True)
    if body is None:
        raise AppError(
            message="Request body must be valid JSON.",
            status_code=400,
            code="INVALID_JSON",
        )

    question = body.get("question", "").strip()
    paper_ids = body.get("paper_ids")
    conversation_id = body.get("conversation_id")

    result = rag_service.answer_query(
        question=question,
        paper_ids=paper_ids,
        conversation_id=conversation_id,
    )

    return jsonify({
        "success": True,
        "data": {
            "answer": result["answer"],
            "sources": result["sources"],
            "conversation_id": result["conversation_id"],
        },
    }), 200
