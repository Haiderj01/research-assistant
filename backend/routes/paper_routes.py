from flask import Blueprint
from backend.controllers.paper_controller import list_papers, get_paper, delete_paper

paper_bp = Blueprint("papers", __name__)

paper_bp.route("/api/v1/papers", methods=["GET"])(list_papers)
paper_bp.route("/api/v1/paper/<string:paper_id>", methods=["GET"])(get_paper)
paper_bp.route("/api/v1/paper/<string:paper_id>", methods=["DELETE"])(delete_paper)
