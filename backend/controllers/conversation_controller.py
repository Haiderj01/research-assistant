from flask import request, jsonify
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import conversation_model


def rename_conversation(conversation_id: str):
    if not ObjectId.is_valid(conversation_id):
        raise AppError(
            message=f"Invalid conversation ID format: '{conversation_id}'.",
            status_code=400,
            code="INVALID_ID",
        )

    body = request.get_json(silent=True)
    if body is None:
        raise AppError(
            message="Request body must be valid JSON.",
            status_code=400,
            code="INVALID_JSON",
        )

    title = (body.get("title") or "").strip()
    if not title:
        raise AppError(
            message="Field 'title' is required and cannot be empty.",
            status_code=400,
            code="MISSING_TITLE",
        )

    conv = conversation_model.get_conversation(conversation_id)
    if not conv:
        raise AppError(
            message=f"No conversation found with ID '{conversation_id}'.",
            status_code=404,
            code="CONVERSATION_NOT_FOUND",
        )

    conversation_model.update_conversation_title(conversation_id, title)

    return jsonify({
        "success": True,
        "data": {"id": conversation_id, "title": title},
        "message": "Conversation renamed successfully.",
    }), 200
