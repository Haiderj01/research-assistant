from flask import Blueprint
from backend.controllers.paper_controller import list_papers, get_paper, delete_paper
from backend.middlewares.auth_middleware import require_auth

paper_bp = Blueprint("papers", __name__)

paper_bp.route("/api/v1/papers", methods=["GET"])(require_auth(list_papers))
paper_bp.route("/api/v1/paper/<string:paper_id>", methods=["GET"])(require_auth(get_paper))
paper_bp.route("/api/v1/paper/<string:paper_id>", methods=["DELETE"])(require_auth(delete_paper))
