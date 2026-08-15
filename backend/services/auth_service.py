import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import bcrypt
import certifi
import jwt
import dns.resolver

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from backend.config import settings
from backend.middlewares.error_handler import AppError
from backend.models import user_model
from backend.utils.logger import logger

TOKEN_EXPIRY_DAYS = 7
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MIN_PASSWORD_LENGTH = 8
_DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "guerrillamail.com",
    "tempmail.com",
    "10minutemail.com",
    "throwawaymail.com",
    "yopmail.com",
    "sharklasers.com",
    "trashmail.com",
    "getnada.com",
    "maildrop.cc",
    "dispostable.com",
    "inboxbear.com",
    "discard.email",
    "emailfake.com",
    "mailnesia.com",
    "mohmal.com",
    "disposable-email.com",
}
_DNS_TIMEOUT_SECONDS = 3


def _domain_has_mail_records(domain: str) -> bool:
    """Return True if a domain can receive email.

    Checks for a resolvable MX record first, then falls back to A/AAAA
    records (some valid mail domains rely on implicit delivery without MX).

    Args:
        domain: The domain part of an email address (lowercased).

    Returns:
        True if the domain has mail/routing records, False otherwise.

    Raises:
        AppError: If the domain name itself is malformed.
    """
    domain = domain.strip().lower()
    if not domain or not re.match(r"^[a-z0-9.-]+\.[a-z]{2,}$", domain):
        raise AppError(
            message="Please provide a valid email address.",
            status_code=422,
            code="INVALID_EMAIL",
        )

    resolver = dns.resolver.Resolver()
    resolver.timeout = _DNS_TIMEOUT_SECONDS
    resolver.lifetime = _DNS_TIMEOUT_SECONDS

    for rtype in ("MX", "A", "AAAA"):
        try:
            answers = resolver.resolve(domain, rtype)
            if answers:
                return True
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            continue
        except dns.resolver.LifetimeTimeout:
            break
        except Exception:
            continue
    return False


def _validate_email(email: str) -> str:
    """Validate and normalize an email address.

    Checks syntax, rejects disposable domains, and verifies the domain
    can receive email via a DNS lookup.

    Args:
        email: The raw email submitted by the user.

    Returns:
        The normalized (lowercased, trimmed) email.

    Raises:
        AppError: If the email is empty, malformed, uses a disposable
        domain, or its domain cannot receive email.
    """
    email = (email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise AppError(
            message="Please provide a valid email address.",
            status_code=422,
            code="INVALID_EMAIL",
        )

    domain = email.split("@", 1)[1]
    if domain in _DISPOSABLE_DOMAINS:
        raise AppError(
            message="Please use a real, non-disposable email address.",
            status_code=422,
            code="DISPOSABLE_EMAIL",
        )

    if not _domain_has_mail_records(domain):
        raise AppError(
            message="The email domain does not appear to accept email.",
            status_code=422,
            code="INVALID_EMAIL_DOMAIN",
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


# ---------------------------------------------------------------------------
# Google OAuth (Sign in with Google)
# ---------------------------------------------------------------------------

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
_OAUTH_STATE_TTL_MINUTES = 10


def google_oauth_configured() -> bool:
    """Return True when both Google OAuth credentials are set."""
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def _oauth_state() -> str:
    """Stateless CSRF token for the OAuth flow.

    Signed with the JWT secret so the callback can verify the request
    actually originated from our consent redirect.
    """
    payload = {
        "purpose": "google_oauth",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=_OAUTH_STATE_TTL_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")


def verify_oauth_state(state: str) -> None:
    """Reject callbacks whose state token is missing, stale, or forged.

    Raises:
        AppError: If the state token is invalid or expired.
    """
    try:
        payload = jwt.decode(state, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("purpose") != "google_oauth":
            raise jwt.InvalidTokenError
    except jwt.InvalidTokenError:
        raise AppError(
            message="This sign-in link is invalid or expired. Please try again.",
            status_code=400,
            code="INVALID_OAUTH_STATE",
        )


def google_auth_url(redirect_uri: str) -> str:
    """Build the Google OAuth consent-screen URL.

    Args:
        redirect_uri: The callback URL registered in Google Cloud Console.

    Returns:
        The full authorization URL to redirect the browser to.
    """
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": _oauth_state(),
        "prompt": "select_account",
    }
    return GOOGLE_AUTH_ENDPOINT + "?" + urllib.parse.urlencode(params)


def exchange_google_code(code: str, redirect_uri: str) -> str:
    """Exchange an authorization code for a Google ID token.

    Args:
        code: The one-time authorization code from the callback.
        redirect_uri: Must match the URI used for the authorization request.

    Returns:
        The raw Google ID token (a JWT).

    Raises:
        AppError: If Google rejects the code or the exchange fails.
    """
    body = urllib.parse.urlencode({
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    request = urllib.request.Request(
        GOOGLE_TOKEN_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    # Some macOS/Python builds have no usable system CA store; certifi's
    # bundle is already a dependency, so use it explicitly.
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with urllib.request.urlopen(request, timeout=10, context=ssl_context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:300]
        logger.warning(f"Google token exchange HTTP {err.code}: {detail}")
        raise AppError(
            message="Could not complete Google sign-in. Please try again.",
            status_code=502,
            code="GOOGLE_TOKEN_EXCHANGE_FAILED",
        )
    except (urllib.error.URLError, TimeoutError, ssl.SSLError, json.JSONDecodeError) as err:
        logger.warning(f"Google token exchange failed: {err}")
        raise AppError(
            message="Could not complete Google sign-in. Please try again.",
            status_code=502,
            code="GOOGLE_TOKEN_EXCHANGE_FAILED",
        )

    token = payload.get("id_token")
    if not token:
        logger.warning(f"Google token exchange returned no id_token: {str(payload)[:200]}")
        raise AppError(
            message="Google did not return an identity token.",
            status_code=502,
            code="GOOGLE_TOKEN_EXCHANGE_FAILED",
        )
    return token


def verify_google_id_token(raw_token: str) -> dict:
    """Verify a Google ID token and extract the verified profile.

    Args:
        raw_token: The ID token returned by Google.

    Returns:
        A dict with ``email`` and ``name`` from the verified profile.

    Raises:
        AppError: If the token is invalid or the email is unverified.
    """
    try:
        info = id_token.verify_oauth2_token(
            raw_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except Exception:
        raise AppError(
            message="Google sign-in verification failed.",
            status_code=401,
            code="INVALID_GOOGLE_TOKEN",
        )

    if not info.get("email_verified"):
        raise AppError(
            message="Google could not verify this email address.",
            status_code=401,
            code="GOOGLE_EMAIL_UNVERIFIED",
        )

    email = (info.get("email") or "").strip().lower()
    if not email:
        raise AppError(
            message="Google did not return an email address.",
            status_code=401,
            code="GOOGLE_EMAIL_MISSING",
        )

    return {
        "email": email,
        "name": (info.get("name") or "").strip(),
    }


def login_or_register_google(profile: dict) -> dict:
    """Log in an existing account or create a Google-originated one.

    A verified Google email is trusted, so it bypasses the disposable/DNS
    email checks used for self-registration.

    Args:
        profile: Dict with ``email`` and ``name`` from the verified token.

    Returns:
        A dict with ``token`` and ``user`` payload, plus ``created``
        indicating whether a new account was created.

    Raises:
        AppError: If the database is unavailable.
    """
    existing = user_model.get_user_by_email(profile["email"])
    if existing is not None:
        token = generate_token(str(existing["_id"]))
        logger.info(f"Google sign-in for existing user {profile['email']}")
        return {"token": token, "user": _user_payload(existing), "created": False}

    user = user_model.create_user(
        profile["email"],
        None,
        profile["name"],
        auth_provider="google",
    )
    if user is None:
        raise AppError(
            message="Could not create account. Please try again later.",
            status_code=500,
            code="DB_UNAVAILABLE",
        )

    token = generate_token(str(user["_id"]))
    logger.info(f"Registered Google user {user['email']}")
    return {"token": token, "user": _user_payload(user), "created": True}
