from flask import Blueprint
from backend.controllers.query_controller import handle_ask
from backend.middlewares.auth_middleware import require_auth

query_bp = Blueprint("query", __name__)

query_bp.route("/api/v1/ask", methods=["POST"])(require_auth(handle_ask))
