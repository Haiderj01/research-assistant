from flask import request, jsonify, g
from backend.middlewares.error_handler import AppError
from backend.services import gap_analysis_service


def handle_gap_analysis():
    body = request.get_json(silent=True)
    if body is None:
        raise AppError(
            message="Request body must be valid JSON.",
            status_code=400,
            code="INVALID_JSON",
        )

    paper_ids = body.get("paper_ids")
    user_id = getattr(g, "user_id", None)

    result = gap_analysis_service.analyze_research_gaps(paper_ids, user_id)

    return jsonify({
        "success": True,
        "data": {
            "gaps": result["gaps"],
            "per_paper_summaries": result["per_paper_summaries"],
        },
    }), 200
