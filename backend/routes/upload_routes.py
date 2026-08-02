from flask import Blueprint
from backend.controllers.upload_controller import handle_upload
from backend.middlewares.auth_middleware import require_auth

upload_bp = Blueprint("upload", __name__)

upload_bp.route("/api/v1/upload", methods=["POST"])(require_auth(handle_upload))
