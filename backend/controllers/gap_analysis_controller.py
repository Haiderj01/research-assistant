from flask import jsonify, g
from backend.controllers._helpers import require_json_body
from backend.services import gap_analysis_service


def handle_gap_analysis():
    body = require_json_body()

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
