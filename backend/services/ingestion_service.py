import os
import uuid
import threading
from werkzeug.utils import secure_filename
from backend.config import settings
from backend.services import pdf_service, chunking_service, embedding_service
from backend.services.vector_store_service import vector_store
from backend.models import paper_model, chunk_model
from backend.middlewares.error_handler import AppError
from backend.utils.logger import logger

_jobs = []
_jobs_lock = threading.Lock()
_jobs_event = threading.Event()


def _process_single(file_path: str, paper_id: str):
    """Run the full ingestion pipeline for one paper."""
    try:
        extraction = pdf_service.process_pdf(file_path)
        paper_model.update_paper(paper_id, {"page_count": extraction["total_pages"]})

        chunks = chunking_service.chunk_paper(
            pages=extraction["pages"],
            chunk_size=settings.DEFAULT_CHUNK_SIZE,
            overlap=settings.DEFAULT_CHUNK_OVERLAP,
        )

        chunk_texts = [c["text"] for c in chunks]
        chunk_vectors = embedding_service.generate_embeddings_batch(chunk_texts)

        chunk_ids = [f"{paper_id}_{c['chunk_index']}" for c in chunks]
        vector_store.add_vectors(chunk_vectors, chunk_ids)

        chunk_model.create_chunks([
            {
                "paper_id": paper_id,
                "chunk_text": c["text"],
                "chunk_index": c["chunk_index"],
                "page_number": c.get("page_number"),
                "vector_id": chunk_ids[i],
            }
            for i, c in enumerate(chunks)
        ])

        paper_model.update_paper(paper_id, {"status": "processed"})
        logger.info(f"Paper {paper_id} processed: {len(chunks)} chunks, {len(chunk_vectors)} vectors")

    except Exception:
        logger.exception(f"Background processing failed for paper {paper_id}")
        paper_model.update_paper(paper_id, {"status": "failed"})


def _worker_loop():
    """Single worker: processes queued files one at a time, smallest first."""
    while True:
        _jobs_event.wait()
        _jobs_event.clear()
        job = None
        with _jobs_lock:
            if _jobs:
                _jobs.sort(key=lambda j: j["file_size"])
                job = _jobs.pop(0)
            if _jobs:
                _jobs_event.set()
        if job:
            _process_single(job["file_path"], job["paper_id"])


_worker = threading.Thread(target=_worker_loop, daemon=True)
_worker.start()


def save_and_queue(file, user_id: str = None) -> dict:
    """Save the uploaded file and queue background processing.

    Returns a paper record immediately with status 'pending'.
    The full pipeline (chunking, embedding, indexing) runs in a
    single background worker that processes files one at a time,
    smallest file first.

    Args:
        file: A werkzeug FileStorage object from the upload request.
        user_id: The authenticated user's ID owning the upload, if any.

    Returns:
        A dict with the created paper record (status: pending).
    """
    original_filename = secure_filename(file.filename or "untitled.pdf")
    if not original_filename.lower().endswith(".pdf"):
        raise AppError(
            message="Only PDF files are supported.",
            status_code=422,
            code="INVALID_FILE_TYPE",
        )

    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{original_filename}"
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, unique_name)
    file.save(file_path)

    paper_title = original_filename.replace(".pdf", "").replace("_", " ").title()
    paper = paper_model.create_paper(
        title=paper_title,
        filename=original_filename,
        file_path=file_path,
        user_id=user_id,
    )
    if not paper:
        os.unlink(file_path)
        raise AppError(
            message="Could not create paper record. Database may be unavailable.",
            status_code=500,
            code="DB_UNAVAILABLE",
        )

    paper_id = str(paper["_id"])
    file_size = os.path.getsize(file_path)

    with _jobs_lock:
        _jobs.append({"file_path": file_path, "paper_id": paper_id, "file_size": file_size})
        _jobs.sort(key=lambda j: j["file_size"])
        _jobs_event.set()

    return paper_model.get_paper(paper_id)
