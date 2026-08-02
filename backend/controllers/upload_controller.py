from flask import request, jsonify, g
from backend.middlewares.error_handler import AppError
from backend.services import ingestion_service
from backend.utils.logger import logger


def handle_upload():
    user_id = getattr(g, "user_id", None)
    if "files" not in request.files:
        raise AppError(
            message="No files provided. Attach at least one PDF file under the 'files' field.",
            status_code=400,
            code="MISSING_FILES",
        )

    files = request.files.getlist("files")
    if not files or not any(f.filename for f in files):
        raise AppError(
            message="No files provided. Attach at least one PDF file.",
            status_code=400,
            code="MISSING_FILES",
        )

    processed = []
    failed = []

    for file in files:
        if not file.filename:
            continue
        try:
            paper = ingestion_service.save_and_queue(file, user_id=user_id)
            processed.append(paper)
        except AppError:
            raise
        except Exception as exc:
            logger.exception(f"Upload handling failed for {file.filename}")
            failed.append({"filename": file.filename, "error": str(exc)})

    if not processed and failed:
        raise AppError(
            message="All uploaded files failed to process.",
            status_code=422,
            code="ALL_FILES_FAILED",
        )

    papers_data = []
    for p in processed:
        papers_data.append({
            "id": str(p["_id"]),
            "title": p["title"],
            "status": p["status"],
            "page_count": p.get("page_count", 0),
            "upload_date": p["upload_date"].isoformat() if hasattr(p.get("upload_date"), "isoformat") else str(p.get("upload_date", "")),
        })

    response = {
        "success": True,
        "data": {
            "papers": papers_data,
        },
        "message": f"{len(processed)} paper(s) uploaded and processed successfully."
        if not failed
        else f"{len(processed)} paper(s) processed; {len(failed)} file(s) failed.",
    }

    return jsonify(response), 201
