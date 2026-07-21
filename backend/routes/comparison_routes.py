from flask import Blueprint
from backend.controllers.comparison_controller import handle_compare

comparison_bp = Blueprint("comparison", __name__)

comparison_bp.route("/api/v1/compare", methods=["POST"])(handle_compare)
