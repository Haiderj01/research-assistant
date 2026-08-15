from flask import Blueprint
from backend.controllers.auth_controller import (
    handle_register,
    handle_login,
    handle_me,
    handle_google_login,
    handle_google_callback,
)
from backend.controllers.paper_controller import list_papers, get_paper, delete_paper
from backend.controllers.query_controller import handle_ask
from backend.controllers.upload_controller import handle_upload
from backend.controllers.history_controller import get_history
from backend.controllers.conversation_controller import rename_conversation, get_conversation_messages
from backend.controllers.summary_controller import handle_summarize
from backend.controllers.comparison_controller import handle_compare
from backend.controllers.gap_analysis_controller import handle_gap_analysis
from backend.middlewares.auth_middleware import require_auth

auth_bp = Blueprint("auth", __name__)
api_bp = Blueprint("api", __name__)

auth_bp.route("/api/v1/auth/register", methods=["POST"])(handle_register)
auth_bp.route("/api/v1/auth/login", methods=["POST"])(handle_login)
auth_bp.route("/api/v1/auth/google", methods=["GET"])(handle_google_login)
auth_bp.route("/api/v1/auth/google/callback", methods=["GET"])(handle_google_callback)
auth_bp.route("/api/v1/auth/me", methods=["GET"])(require_auth(handle_me))

api_bp.route("/api/v1/papers", methods=["GET"])(require_auth(list_papers))
api_bp.route("/api/v1/paper/<string:paper_id>", methods=["GET"])(require_auth(get_paper))
api_bp.route("/api/v1/paper/<string:paper_id>", methods=["DELETE"])(require_auth(delete_paper))
api_bp.route("/api/v1/ask", methods=["POST"])(require_auth(handle_ask))
api_bp.route("/api/v1/upload", methods=["POST"])(require_auth(handle_upload))
api_bp.route("/api/v1/history", methods=["GET"])(require_auth(get_history))
api_bp.route("/api/v1/conversation/<string:conversation_id>", methods=["PATCH"])(require_auth(rename_conversation))
api_bp.route("/api/v1/conversation/<string:conversation_id>/messages", methods=["GET"])(require_auth(get_conversation_messages))
api_bp.route("/api/v1/summarize", methods=["POST"])(require_auth(handle_summarize))
api_bp.route("/api/v1/compare", methods=["POST"])(require_auth(handle_compare))
api_bp.route("/api/v1/gap-analysis", methods=["POST"])(require_auth(handle_gap_analysis))