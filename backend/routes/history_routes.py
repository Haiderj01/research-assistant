from flask import Blueprint
from backend.controllers.history_controller import get_history

history_bp = Blueprint("history", __name__)

history_bp.route("/api/v1/history", methods=["GET"])(get_history)
