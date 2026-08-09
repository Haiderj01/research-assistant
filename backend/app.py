from flask import Flask, jsonify
from flask_cors import CORS
from backend.config import settings
from backend.middlewares.error_handler import register_error_handlers
from backend.services.database_service import DatabaseService
from backend.services.vector_store_service import vector_store
from backend.services.embedding_service import preload_model
from backend.routes import api_bp, auth_bp
from backend.utils.logger import logger


def _prune_stale_vectors() -> None:
    """Remove vectors whose chunks no longer exist in the database.

    The FAISS index is persisted across restarts, but the database may be
    reset (e.g. in-memory mock) or documents may be deleted. Stale vectors
    pollute similarity search and cause valid papers to be out-ranked.
    """
    chunks = DatabaseService.get_collection("chunks")
    if chunks is None:
        logger.warning("Skipping vector prune: database unavailable.")
        return

    try:
        db_chunk_ids = {
            str(doc["vector_id"])
            for doc in chunks.find({}, {"vector_id": 1})
            if doc.get("vector_id")
        }
    except Exception:
        logger.exception("Skipping vector prune: failed to read chunk IDs.")
        return

    stale = vector_store.list_chunk_ids() - db_chunk_ids
    if stale:
        vector_store.remove_vectors(list(stale))
        logger.info(f"Pruned {len(stale)} stale vectors from store")


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    app.config["UPLOAD_FOLDER"] = settings.UPLOAD_DIRECTORY

    register_error_handlers(app)
    preload_model()
    _prune_stale_vectors()

    @app.route("/api/v1/health", methods=["GET"])
    def health_check():
        db_ok = DatabaseService.is_connected()
        vs_ok = vector_store.is_available()
        all_ok = db_ok and vs_ok
        return jsonify({
            "success": all_ok,
            "data": {
                "status": "healthy" if all_ok else "degraded",
                "database": "connected" if db_ok else "unavailable",
                "vector_store": "available" if vs_ok else "unavailable",
            },
        }), 200 if all_ok else 503

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == "__main__":
    settings.validate_required()
    app = create_app()
    logger.info(f"Starting server on port {settings.APPLICATION_PORT}")
    app.run(host="0.0.0.0", port=settings.APPLICATION_PORT, debug=settings.DEBUG_MODE)
