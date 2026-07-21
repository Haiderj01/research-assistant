from datetime import datetime, timezone
from bson import ObjectId
from backend.services.database_service import DatabaseService


def create_question(
    conversation_id: str,
    question_text: str,
    answer_text: str,
    source_chunk_ids: list[str],
) -> dict:
    coll = DatabaseService.get_collection("questions")
    if coll is None:
        return None
    doc = {
        "conversation_id": ObjectId(conversation_id),
        "question_text": question_text,
        "answer_text": answer_text,
        "source_chunk_ids": [ObjectId(cid) for cid in source_chunk_ids],
        "created_at": datetime.now(timezone.utc),
    }
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_questions_by_conversation(conversation_id: str) -> list[dict]:
    coll = DatabaseService.get_collection("questions")
    if coll is None:
        return []
    return list(
        coll.find({"conversation_id": ObjectId(conversation_id)})
        .sort("created_at", 1)
    )
