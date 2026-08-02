from flask import Blueprint
from backend.controllers.comparison_controller import handle_compare
from backend.middlewares.auth_middleware import require_auth

comparison_bp = Blueprint("comparison", __name__)

comparison_bp.route("/api/v1/compare", methods=["POST"])(require_auth(handle_compare))
