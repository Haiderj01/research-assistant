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


def _to_object_id(value: str):
    if not value:
        return None
    try:
        return ObjectId(value)
    except Exception:
        return None


def get_conversation(conversation_id: str, user_id: str = None) -> dict:
    coll = DatabaseService.get_collection("conversations")
    if coll is None:
        return None
    query = {"_id": ObjectId(conversation_id)}
    uid = _to_object_id(user_id)
    if user_id and uid is None:
        return None
    if uid is not None:
        query["user_id"] = uid
    return coll.find_one(query)


def get_all_conversations(limit: int = 50, user_id: str = None) -> list[dict]:
    coll = DatabaseService.get_collection("conversations")
    if coll is None:
        return []
    query = {}
    uid = _to_object_id(user_id)
    if user_id and uid is None:
        return []
    if uid is not None:
        query["user_id"] = uid
    return list(coll.find(query).sort("updated_at", -1).limit(limit))


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
