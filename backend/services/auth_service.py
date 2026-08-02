import re
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.config.settings import settings
from backend.middlewares.error_handler import AppError
from backend.models import user_model
from backend.utils.logger import logger

TOKEN_EXPIRY_DAYS = 7
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MIN_PASSWORD_LENGTH = 8


def _validate_email(email: str) -> str:
    """Validate and normalize an email address.

    Args:
        email: The raw email submitted by the user.

    Returns:
        The normalized (lowercased, trimmed) email.

    Raises:
        AppError: If the email is empty or malformed.
    """
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise AppError(
            message="Please provide a valid email address.",
            status_code=422,
            code="INVALID_EMAIL",
        )
    return email


def _validate_password(password: str) -> None:
    """Validate that a password meets the minimum strength policy.

    Args:
        password: The raw password submitted by the user.

    Raises:
        AppError: If the password is missing or too weak.
    """
    if not password:
        raise AppError(
            message="Password is required.",
            status_code=400,
            code="MISSING_PASSWORD",
        )
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise AppError(
            message=f"Password must be at least {_MIN_PASSWORD_LENGTH} characters long.",
            status_code=422,
            code="WEAK_PASSWORD",
        )


def _validate_name(name: str) -> str:
    """Validate and normalize a display name.

    Args:
        name: The raw display name submitted by the user.

    Returns:
        The trimmed display name.

    Raises:
        AppError: If the name is provided but too long.
    """
    name = (name or "").strip()
    if len(name) > 80:
        raise AppError(
            message="Name must be at most 80 characters long.",
            status_code=422,
            code="INVALID_NAME",
        )
    return name


def generate_token(user_id: str) -> str:
    """Generate a signed JWT for a user.

    Args:
        user_id: The user's ObjectId as a string.

    Returns:
        A JWT string valid for TOKEN_EXPIRY_DAYS.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(days=TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> str:
    """Verify a JWT and return the embedded user_id.

    Args:
        token: The JWT string from the Authorization header.

    Returns:
        The user_id (subject) stored in the token.

    Raises:
        AppError: If the token is missing, malformed, expired, or invalid.
    """
    if not token:
        raise AppError(
            message="Authentication token is missing.",
            status_code=401,
            code="UNAUTHORIZED",
        )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AppError(
            message="Your session has expired. Please log in again.",
            status_code=401,
            code="TOKEN_EXPIRED",
        )
    except jwt.InvalidTokenError:
        raise AppError(
            message="Invalid or malformed authentication token.",
            status_code=401,
            code="INVALID_TOKEN",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise AppError(
            message="Invalid authentication token.",
            status_code=401,
            code="INVALID_TOKEN",
        )
    return str(user_id)


def _user_payload(user: dict) -> dict:
    """Build the public user payload for API responses.

    Args:
        user: A user document from the database.

    Returns:
        A dict with id, name, email, and created_at.
    """
    return {
        "id": str(user["_id"]),
        "name": (user.get("name") or "").strip(),
        "email": user["email"],
        "created_at": user["created_at"].isoformat()
        if hasattr(user.get("created_at"), "isoformat")
        else str(user.get("created_at", "")),
    }


def register_user(email: str, password: str, name: str = "") -> dict:
    """Create a new user account and return an auth token.

    Args:
        email: The user's email address.
        password: The user's chosen password.
        name: The user's display name (optional).

    Returns:
        A dict with ``token`` and ``user`` payload.

    Raises:
        AppError: On weak password, malformed email, or duplicate email.
    """
    email = _validate_email(email)
    _validate_password(password)
    name = _validate_name(name)

    existing = user_model.get_user_by_email(email)
    if existing is not None:
        raise AppError(
            message="An account with this email already exists.",
            status_code=409,
            code="EMAIL_ALREADY_REGISTERED",
        )

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = user_model.create_user(email, password_hash, name)
    if user is None:
        raise AppError(
            message="Could not create account. Please try again later.",
            status_code=500,
            code="DB_UNAVAILABLE",
        )

    token = generate_token(str(user["_id"]))
    logger.info(f"Registered user {user['email']}")
    return {"token": token, "user": _user_payload(user)}


def login_user(email: str, password: str) -> dict:
    """Authenticate a user and return an auth token.

    Args:
        email: The user's email address.
        password: The user's password.

    Returns:
        A dict with ``token`` and ``user`` payload.

    Raises:
        AppError: With a generic message if credentials are invalid.
    """
    email = (email or "").strip().lower()
    user = user_model.get_user_by_email(email) if email else None

    valid = user is not None and user.get("password_hash") and bcrypt.checkpw(
        password.encode("utf-8"),
        user["password_hash"].encode("utf-8"),
    )
    if not valid:
        raise AppError(
            message="Invalid email or password.",
            status_code=401,
            code="INVALID_CREDENTIALS",
        )

    token = generate_token(str(user["_id"]))
    logger.info(f"User logged in: {user['email']}")
    return {"token": token, "user": _user_payload(user)}
