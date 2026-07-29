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


def get_paper(paper_id: str) -> dict:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return None
    return coll.find_one({"_id": ObjectId(paper_id)})


def get_all_papers(status: str = None) -> list[dict]:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return []
    query = {}
    if status:
        query["status"] = status
    return list(coll.find(query).sort("upload_date", -1))


def update_paper(paper_id: str, updates: dict) -> bool:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return False
    result = coll.update_one({"_id": ObjectId(paper_id)}, {"$set": updates})
    return result.modified_count > 0


def delete_paper(paper_id: str) -> bool:
    coll = DatabaseService.get_collection("papers")
    if coll is None:
        return False
    result = coll.delete_one({"_id": ObjectId(paper_id)})
    return result.deleted_count > 0
