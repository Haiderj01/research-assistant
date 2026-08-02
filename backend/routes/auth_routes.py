from flask import Blueprint
from backend.controllers.auth_controller import handle_register, handle_login

auth_bp = Blueprint("auth", __name__)

auth_bp.route("/api/v1/auth/register", methods=["POST"])(handle_register)
auth_bp.route("/api/v1/auth/login", methods=["POST"])(handle_login)
