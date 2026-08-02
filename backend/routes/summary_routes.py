from flask import Blueprint
from backend.controllers.summary_controller import handle_summarize
from backend.middlewares.auth_middleware import require_auth

summary_bp = Blueprint("summary", __name__)

summary_bp.route("/api/v1/summarize", methods=["POST"])(require_auth(handle_summarize))
