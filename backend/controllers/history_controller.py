from flask import request, jsonify
from backend.models import conversation_model, question_model, search_history_model


def get_history():
    try:
        limit = int(request.args.get("limit", 50))
    except (ValueError, TypeError):
        limit = 50

    conversations = conversation_model.get_all_conversations(limit=limit)

    conversations_data = []
    for c in conversations:
        conversations_data.append({
            "id": str(c["_id"]),
            "title": c.get("title", ""),
            "paper_ids": [str(pid) for pid in c.get("paper_ids", [])],
            "created_at": c["created_at"].isoformat() if hasattr(c.get("created_at"), "isoformat") else str(c.get("created_at", "")),
            "updated_at": c["updated_at"].isoformat() if hasattr(c.get("updated_at"), "isoformat") else str(c.get("updated_at", "")),
        })

    search_history = search_history_model.get_search_history(limit=limit)
    search_data = []
    for s in search_history:
        search_data.append({
            "id": str(s["_id"]),
            "query_text": s.get("query_text", ""),
            "paper_ids": [str(pid) for pid in s.get("paper_ids", [])],
            "created_at": s["created_at"].isoformat() if hasattr(s.get("created_at"), "isoformat") else str(s.get("created_at", "")),
        })

    return jsonify({
        "success": True,
        "data": {
            "conversations": conversations_data,
            "search_history": search_data,
        },
    }), 200
