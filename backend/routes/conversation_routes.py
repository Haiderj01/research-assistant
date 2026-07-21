from flask import Blueprint
from backend.controllers.conversation_controller import rename_conversation

conversation_bp = Blueprint("conversations", __name__)

conversation_bp.route("/api/v1/conversation/<string:conversation_id>", methods=["PATCH"])(rename_conversation)
