from flask import Blueprint
from backend.controllers.query_controller import handle_ask

query_bp = Blueprint("query", __name__)

query_bp.route("/api/v1/ask", methods=["POST"])(handle_ask)
