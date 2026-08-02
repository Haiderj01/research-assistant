from datetime import datetime, timezone
from bson import ObjectId
from backend.services.database_service import DatabaseService


def create_search_entry(
    query_text: str,
    paper_ids: list[str],
    result_chunk_ids: list[str],
    user_id: str = None,
) -> dict:
    coll = DatabaseService.get_collection("search_history")
    if coll is None:
        return None
    doc = {
        "query_text": query_text,
        "paper_ids": [ObjectId(pid) for pid in paper_ids],
        "result_chunk_ids": [ObjectId(cid) for cid in result_chunk_ids],
        "created_at": datetime.now(timezone.utc),
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


def get_search_history(limit: int = 50, user_id: str = None) -> list[dict]:
    coll = DatabaseService.get_collection("search_history")
    if coll is None:
        return []
    query = {}
    uid = _to_object_id(user_id)
    if user_id and uid is None:
        return []
    if uid is not None:
        query["user_id"] = uid
    return list(coll.find(query).sort("created_at", -1).limit(limit))
