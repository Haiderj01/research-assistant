from flask import Blueprint
from backend.controllers.summary_controller import handle_summarize

summary_bp = Blueprint("summary", __name__)

summary_bp.route("/api/v1/summarize", methods=["POST"])(handle_summarize)
