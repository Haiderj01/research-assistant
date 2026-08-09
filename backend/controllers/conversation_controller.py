from flask import request, jsonify, g
from backend.controllers._helpers import require_json_body
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import conversation_model, question_model


def rename_conversation(conversation_id: str):
    if not ObjectId.is_valid(conversation_id):
        raise AppError(
            message=f"Invalid conversation ID format: '{conversation_id}'.",
            status_code=400,
            code="INVALID_ID",
        )

    user_id = getattr(g, "user_id", None)

    body = require_json_body()

    title = (body.get("title") or "").strip()
    if not title:
        raise AppError(
            message="Field 'title' is required and cannot be empty.",
            status_code=400,
            code="MISSING_TITLE",
        )

    conv = conversation_model.get_conversation(conversation_id, user_id=user_id)
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


def get_conversation_messages(conversation_id: str):
    if not ObjectId.is_valid(conversation_id):
        raise AppError(
            message=f"Invalid conversation ID format: '{conversation_id}'.",
            status_code=400,
            code="INVALID_ID",
        )

    user_id = getattr(g, "user_id", None)

    conv = conversation_model.get_conversation(conversation_id, user_id=user_id)
    if not conv:
        raise AppError(
            message=f"No conversation found with ID '{conversation_id}'.",
            status_code=404,
            code="CONVERSATION_NOT_FOUND",
        )

    questions = question_model.get_questions_by_conversation(conversation_id, user_id=user_id)
    messages = []
    for q in questions:
        messages.append({"role": "user", "content": q["question_text"]})
        messages.append({"role": "assistant", "content": q["answer_text"]})

    return jsonify({
        "success": True,
        "data": {
            "conversation": {
                "id": str(conv["_id"]),
                "title": conv.get("title", ""),
                "paper_ids": [str(pid) for pid in conv.get("paper_ids", [])],
                "created_at": conv["created_at"].isoformat() if hasattr(conv.get("created_at"), "isoformat") else str(conv.get("created_at", "")),
                "updated_at": conv["updated_at"].isoformat() if hasattr(conv.get("updated_at"), "isoformat") else str(conv.get("updated_at", "")),
            },
            "messages": messages,
        },
    }), 200
