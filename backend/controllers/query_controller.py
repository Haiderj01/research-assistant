from flask import request, jsonify, g
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import paper_model, conversation_model
from backend.services import rag_service


def handle_ask():
    user_id = getattr(g, "user_id", None)
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

    if paper_ids:
        for pid in paper_ids:
            if not ObjectId.is_valid(pid):
                raise AppError(
                    message=f"Invalid paper ID format: '{pid}'.",
                    status_code=400,
                    code="INVALID_ID",
                )
            paper = paper_model.get_paper(pid, user_id=user_id)
            if not paper:
                raise AppError(
                    message=f"No paper found with ID '{pid}'.",
                    status_code=404,
                    code="PAPER_NOT_FOUND",
                )

    if conversation_id:
        if not ObjectId.is_valid(conversation_id):
            raise AppError(
                message=f"Invalid conversation ID format: '{conversation_id}'.",
                status_code=400,
                code="INVALID_ID",
            )
        conv = conversation_model.get_conversation(conversation_id, user_id=user_id)
        if not conv:
            raise AppError(
                message=f"No conversation found with ID '{conversation_id}'.",
                status_code=404,
                code="CONVERSATION_NOT_FOUND",
            )

    result = rag_service.answer_query(
        question=question,
        paper_ids=paper_ids,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    return jsonify({
        "success": True,
        "data": {
            "answer": result["answer"],
            "sources": result["sources"],
            "conversation_id": result["conversation_id"],
        },
    }), 200
