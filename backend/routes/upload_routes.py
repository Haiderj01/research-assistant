from flask import Blueprint
from backend.controllers.upload_controller import handle_upload

upload_bp = Blueprint("upload", __name__)

upload_bp.route("/api/v1/upload", methods=["POST"])(handle_upload)
