from flask import request, jsonify
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import paper_model, chunk_model
from backend.services.vector_store_service import vector_store
from backend.utils.logger import logger


def list_papers():
    status = request.args.get("status")
    if status and status not in ("pending", "processing", "processed", "failed"):
        raise AppError(
            message=f"Invalid status filter '{status}'. Valid values: pending, processing, processed, failed.",
            status_code=400,
            code="INVALID_STATUS",
        )

    papers = paper_model.get_all_papers(status=status)
    papers_data = []
    for p in papers:
        papers_data.append({
            "id": str(p["_id"]),
            "title": p["title"],
            "status": p["status"],
            "page_count": p.get("page_count", 0),
            "upload_date": p["upload_date"].isoformat() if hasattr(p.get("upload_date"), "isoformat") else str(p.get("upload_date", "")),
            "keywords": p.get("keywords", []),
        })

    return jsonify({
        "success": True,
        "data": {"papers": papers_data},
    }), 200


def get_paper(paper_id: str):
    if not ObjectId.is_valid(paper_id):
        raise AppError(
            message=f"Invalid paper ID format: '{paper_id}'.",
            status_code=400,
            code="INVALID_ID",
        )

    paper = paper_model.get_paper(paper_id)
    if not paper:
        raise AppError(
            message=f"No paper found with ID '{paper_id}'.",
            status_code=404,
            code="PAPER_NOT_FOUND",
        )

    return jsonify({
        "success": True,
        "data": {
            "paper": {
                "id": str(paper["_id"]),
                "title": paper["title"],
                "filename": paper["filename"],
                "status": paper["status"],
                "page_count": paper.get("page_count", 0),
                "upload_date": paper["upload_date"].isoformat() if hasattr(paper.get("upload_date"), "isoformat") else str(paper.get("upload_date", "")),
                "keywords": paper.get("keywords", []),
                "datasets": paper.get("datasets", []),
                "algorithms": paper.get("algorithms", []),
                "summary": paper.get("summary", ""),
            },
        },
    }), 200


def delete_paper(paper_id: str):
    if not ObjectId.is_valid(paper_id):
        raise AppError(
            message=f"Invalid paper ID format: '{paper_id}'.",
            status_code=400,
            code="INVALID_ID",
        )

    paper = paper_model.get_paper(paper_id)
    if not paper:
        raise AppError(
            message=f"No paper found with ID '{paper_id}'.",
            status_code=404,
            code="PAPER_NOT_FOUND",
        )

    chunks = chunk_model.get_chunks_by_paper(paper_id)
    vector_ids = [c.get("vector_id") for c in chunks if c.get("vector_id")]
    if vector_ids:
        vector_store.remove_vectors(vector_ids)

    chunk_model.delete_chunks_by_paper(paper_id)
    paper_model.delete_paper(paper_id)

    logger.info(f"Paper {paper_id} and associated data deleted")

    return jsonify({
        "success": True,
        "data": {"deleted_id": paper_id},
        "message": f"Paper '{paper['title']}' deleted successfully.",
    }), 200
