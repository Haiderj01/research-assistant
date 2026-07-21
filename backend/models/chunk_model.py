from datetime import datetime, timezone
from bson import ObjectId
from backend.services.database_service import DatabaseService


def create_chunks(chunks: list[dict]) -> list[dict]:
    """Insert multiple chunk records.

    Each chunk dict must have:
        - paper_id (str)
        - chunk_text (str)
        - chunk_index (int)
        - page_number (int, optional)
        - vector_id (int/str)

    Returns the inserted documents with _id populated.
    """
    coll = DatabaseService.get_collection("chunks")
    if coll is None:
        return None
    docs = []
    for c in chunks:
        docs.append({
            "paper_id": ObjectId(c["paper_id"]),
            "chunk_text": c["chunk_text"],
            "chunk_index": c["chunk_index"],
            "page_number": c.get("page_number"),
            "vector_id": str(c["vector_id"]),
            "created_at": datetime.now(timezone.utc),
        })
    result = coll.insert_many(docs)
    for i, doc in enumerate(docs):
        doc["_id"] = result.inserted_ids[i]
    return docs


def get_chunks_by_paper(paper_id: str) -> list[dict]:
    coll = DatabaseService.get_collection("chunks")
    if coll is None:
        return []
    return list(coll.find({"paper_id": ObjectId(paper_id)}).sort("chunk_index", 1))


def get_chunks_by_ids(chunk_ids: list[str]) -> list[dict]:
    coll = DatabaseService.get_collection("chunks")
    if coll is None:
        return []
    oids = [ObjectId(cid) for cid in chunk_ids]
    return list(coll.find({"_id": {"$in": oids}}))


def get_chunk_by_vector_id(vector_id: str) -> dict:
    coll = DatabaseService.get_collection("chunks")
    if coll is None:
        return None
    return coll.find_one({"vector_id": vector_id})


def delete_chunks_by_paper(paper_id: str) -> int:
    coll = DatabaseService.get_collection("chunks")
    if coll is None:
        return 0
    result = coll.delete_many({"paper_id": ObjectId(paper_id)})
    return result.deleted_count
