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


def get_search_history(limit: int = 50) -> list[dict]:
    coll = DatabaseService.get_collection("search_history")
    if coll is None:
        return []
    return list(coll.find().sort("created_at", -1).limit(limit))
