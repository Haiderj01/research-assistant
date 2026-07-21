from flask import jsonify
from backend.utils.logger import logger


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "BAD_REQUEST"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning(f"AppError: {error.code} | {error.message}")
        return jsonify({
            "success": False,
            "error": {
                "code": error.code,
                "message": error.message,
            },
        }), error.status_code

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
            },
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        return jsonify({
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "The HTTP method is not allowed for this endpoint.",
            },
        }), 405

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            },
        }), 500
