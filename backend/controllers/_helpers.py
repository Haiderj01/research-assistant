from flask import request
from backend.middlewares.error_handler import AppError


def require_json_body() -> dict:
    body = request.get_json(silent=True)
    if body is None:
        raise AppError(
            message="Request body must be valid JSON.",
            status_code=400,
            code="INVALID_JSON",
        )
    return body