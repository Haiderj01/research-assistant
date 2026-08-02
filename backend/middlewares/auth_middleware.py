from functools import wraps
from flask import request, g
from backend.middlewares.error_handler import AppError
from backend.services.auth_service import verify_token


def require_auth(view_func):
    """Protect a Flask view with JWT authentication.

    Reads the ``Authorization: Bearer <token>`` header, verifies the token,
    and attaches the resolved ``user_id`` to ``flask.g.user_id``.

    Raises:
        AppError: 401 if the token is missing, invalid, or expired.
    """

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise AppError(
                message="Authentication required. Please log in.",
                status_code=401,
                code="UNAUTHORIZED",
            )
        token = auth_header[len("Bearer "):].strip()
        user_id = verify_token(token)
        g.user_id = user_id
        return view_func(*args, **kwargs)

    return wrapper
