from flask import Flask, jsonify
from flask_cors import CORS
from backend.config.settings import settings
from backend.middlewares.error_handler import register_error_handlers
from backend.routes.upload_routes import upload_bp
from backend.routes.query_routes import query_bp
from backend.routes.paper_routes import paper_bp
from backend.routes.history_routes import history_bp
from backend.routes.conversation_routes import conversation_bp
from backend.routes.summary_routes import summary_bp
from backend.routes.comparison_routes import comparison_bp
from backend.utils.logger import logger


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = settings.UPLOAD_DIRECTORY

    register_error_handlers(app)

    @app.route("/api/v1/health", methods=["GET"])
    def health_check():
        return jsonify({
            "success": True,
            "data": {
                "status": "healthy",
                "database": "unchecked",
                "vector_store": "unchecked",
            },
        }), 200

    app.register_blueprint(upload_bp)
    app.register_blueprint(query_bp)
    app.register_blueprint(paper_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(comparison_bp)
    app.register_blueprint(conversation_bp)

    return app


if __name__ == "__main__":
    settings.validate_required()
    app = create_app()
    logger.info(f"Starting server on port {settings.APPLICATION_PORT}")
    app.run(host="0.0.0.0", port=settings.APPLICATION_PORT, debug=settings.DEBUG_MODE)
