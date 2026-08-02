from flask import Blueprint
from backend.controllers.gap_analysis_controller import handle_gap_analysis
from backend.middlewares.auth_middleware import require_auth

gap_analysis_bp = Blueprint("gap_analysis", __name__)

gap_analysis_bp.route("/api/v1/gap-analysis", methods=["POST"])(
    require_auth(handle_gap_analysis)
)
