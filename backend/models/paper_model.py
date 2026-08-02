from datetime import datetime, timezone
from bson import ObjectId
from backend.services.database_service import DatabaseService


def create_paper(
    title: str,
    filename: str,
    file_path: str,
    user_id: str = None,
) -> dict:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return None
    doc = {
        "title": title,
        "filename": filename,
        "file_path": file_path,
        "upload_date": datetime.now(timezone.utc),
        "page_count": 0,
        "status": "pending",
        "summary": "",
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


def get_paper(paper_id: str, user_id: str = None) -> dict:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return None
    query = {"_id": ObjectId(paper_id)}
    uid = _to_object_id(user_id)
    if user_id and uid is None:
        return None
    if uid is not None:
        query["user_id"] = uid
    return coll.find_one(query)


def get_all_papers(status: str = None, user_id: str = None) -> list[dict]:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return []
    query = {}
    if status:
        query["status"] = status
    uid = _to_object_id(user_id)
    if user_id and uid is None:
        return []
    if uid is not None:
        query["user_id"] = uid
    return list(coll.find(query).sort("upload_date", -1))


def update_paper(paper_id: str, updates: dict) -> bool:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return False
    result = coll.update_one({"_id": ObjectId(paper_id)}, {"$set": updates})
    return result.modified_count > 0


def delete_paper(paper_id: str, user_id: str = None) -> bool:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return False
    query = {"_id": ObjectId(paper_id)}
    uid = _to_object_id(user_id)
    if user_id and uid is None:
        return False
    if uid is not None:
        query["user_id"] = uid
    result = coll.delete_one(query)
    return result.deleted_count > 0
