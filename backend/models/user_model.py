from datetime import datetime, timezone
from bson import ObjectId
from backend.services.database_service import DatabaseService


def create_user(email: str, password_hash: str | None, name: str = "", auth_provider: str = "password") -> dict:
    """Create a new user account.

    Args:
        email: The user's email address (unique, case-normalized).
        password_hash: The bcrypt-hashed password, or None for accounts
            that authenticate via an external provider (e.g. Google).
        name: The user's display name (optional).
        auth_provider: Where the account originates: "password" or "google".

    Returns:
        The created user document with an ``_id``, or None if the database
        is unavailable.
    """
    coll = DatabaseService.get_collection("users")
    if coll is None:
        return None
    doc = {
        "email": email.lower(),
        "password_hash": password_hash,
        "name": (name or "").strip(),
        "auth_provider": auth_provider,
        "created_at": datetime.now(timezone.utc),
    }
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def get_user_by_email(email: str) -> dict | None:
    """Fetch a user by their email address.

    Args:
        email: The user's email address.

    Returns:
        The matching user document, or None if not found / DB unavailable.
    """
    coll = DatabaseService.get_collection("users")
    if coll is None:
        return None
    return coll.find_one({"email": email.lower()})


def get_user_by_id(user_id: str) -> dict | None:
    """Fetch a user by their ObjectId.

    Args:
        user_id: The user's ObjectId as a string.

    Returns:
        The matching user document, or None if not found / DB unavailable.
    """
    coll = DatabaseService.get_collection("users")
    if coll is None:
        return None
    try:
        return coll.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
