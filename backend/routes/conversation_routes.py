from flask import Blueprint
from backend.controllers.conversation_controller import rename_conversation, get_conversation_messages
from backend.middlewares.auth_middleware import require_auth

conversation_bp = Blueprint("conversations", __name__)

conversation_bp.route("/api/v1/conversation/<string:conversation_id>", methods=["PATCH"])(require_auth(rename_conversation))
conversation_bp.route("/api/v1/conversation/<string:conversation_id>/messages", methods=["GET"])(require_auth(get_conversation_messages))
