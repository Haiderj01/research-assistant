from flask import Blueprint
from backend.controllers.history_controller import get_history
from backend.middlewares.auth_middleware import require_auth

history_bp = Blueprint("history", __name__)

history_bp.route("/api/v1/history", methods=["GET"])(require_auth(get_history))
