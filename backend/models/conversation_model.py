from datetime import datetime, timezone
from bson import ObjectId
from backend.services.database_service import DatabaseService


def create_conversation(paper_ids: list[str], title: str = "", user_id: str = None) -> dict:
    coll = DatabaseService.get_collection("conversations")
    if coll is None:
        return None
    now = datetime.now(timezone.utc)
    doc = {
        "paper_ids": [ObjectId(pid) for pid in paper_ids],
        "title": title,
        "created_at": now,
        "updated_at": now,
        "user_id": ObjectId(user_id) if user_id else None,
    }
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_conversation(conversation_id: str) -> dict:
    coll = DatabaseService.get_collection("conversations")
    if coll is None:
        return None
    return coll.find_one({"_id": ObjectId(conversation_id)})


def get_all_conversations(limit: int = 50) -> list[dict]:
    coll = DatabaseService.get_collection("conversations")
    if coll is None:
        return []
    return list(coll.find().sort("updated_at", -1).limit(limit))


def update_conversation(conversation_id: str) -> bool:
    coll = DatabaseService.get_collection("conversations")
    if coll is None:
        return False
    result = coll.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {"updated_at": datetime.now(timezone.utc)}},
    )
    return result.modified_count > 0


def update_conversation_title(conversation_id: str, title: str) -> bool:
    coll = DatabaseService.get_collection("conversations")
    if coll is None:
        return False
    now = datetime.now(timezone.utc)
    result = coll.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {"title": title, "updated_at": now}},
    )
    return result.modified_count > 0
