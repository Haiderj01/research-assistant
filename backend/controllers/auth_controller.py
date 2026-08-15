from flask import jsonify, redirect, request, g
from backend.controllers._helpers import require_json_body
from backend.services import auth_service
from backend.middlewares.error_handler import AppError
from backend.config import settings
from backend.models import user_model


def _google_redirect_uri() -> str:
    """The callback URL, derived from the backend's own host.

    Must match exactly the redirect URI registered in Google Cloud Console.
    """
    return request.url_root.rstrip("/") + "/api/v1/auth/google/callback"


def _require_google_configured() -> None:
    if not auth_service.google_oauth_configured():
        raise AppError(
            message="Google sign-in is not configured on this server.",
            status_code=503,
            code="GOOGLE_NOT_CONFIGURED",
        )


def handle_register():
    body = require_json_body()

    email = body.get("email")
    password = body.get("password")
    name = body.get("name")

    result = auth_service.register_user(email, password, name)

    return jsonify({
        "success": True,
        "data": {
            "token": result["token"],
            "user": result["user"],
        },
        "message": "Account created successfully.",
    }), 201


def handle_login():
    body = require_json_body()

    email = body.get("email")
    password = body.get("password")

    result = auth_service.login_user(email, password)

    return jsonify({
        "success": True,
        "data": {
            "token": result["token"],
            "user": result["user"],
        },
        "message": "Login successful.",
    }), 200


def handle_me():
    user_id = getattr(g, "user_id", None)
    user = user_model.get_user_by_id(user_id) if user_id else None
    if user is None:
        raise AppError(
            message="Account not found.",
            status_code=404,
            code="USER_NOT_FOUND",
        )
    return jsonify({
        "success": True,
        "data": {"user": auth_service._user_payload(user)},
    }), 200


def handle_google_login():
    _require_google_configured()
    return redirect(auth_service.google_auth_url(_google_redirect_uri()), 302)


def handle_google_callback():
    _require_google_configured()

    if request.args.get("error"):
        raise AppError(
            message="Google sign-in was cancelled or denied.",
            status_code=400,
            code="GOOGLE_AUTH_ERROR",
        )

    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        raise AppError(
            message="Missing authorization code.",
            status_code=400,
            code="MISSING_OAUTH_CODE",
        )

    auth_service.verify_oauth_state(state)
    raw_token = auth_service.exchange_google_code(code, _google_redirect_uri())
    profile = auth_service.verify_google_id_token(raw_token)
    result = auth_service.login_or_register_google(profile)

    frontend = settings.FRONTEND_URL.rstrip("/")
    return redirect(f"{frontend}/oauth/callback?token={result['token']}", 302)
