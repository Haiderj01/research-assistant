from flask import request, jsonify, g
from backend.controllers._helpers import require_json_body
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import paper_model, chunk_model
from backend.services import gemini_service
from backend.config import settings
import time

# Gemini 3.6 Flash free-tier limits (docs / AI Studio): input TPM is
# generous (~1M+), so the binding constraint is RPM ~15 -> ~4s spacing.
_TPM_LIMIT = 1_000_000
_RPM_LIMIT = 15
# Measured: 32,000 chars of paper text ~= 9,186 tokens.
_CHARS_PER_TOKEN = 3.5
# Input-token budget per map call. Gemini's context window is 1M tokens, so
# batches can be far larger than Groq's; this keeps multi-batch papers rare.
_MAP_INPUT_TOKEN_BUDGET = int(_TPM_LIMIT * 0.05)
_OUTPUT_TOKEN_ALLOWANCE = 2048
_TEMPLATE_OVERHEAD_TOKENS = 200
_MIN_BATCH_DELAY_SECONDS = 60.0 / _RPM_LIMIT
_HEADER_TOKEN_ALLOWANCE = 150


def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / _CHARS_PER_TOKEN))


def _batch_chunks(chunks: list[dict], budget_tokens: int) -> list[list[dict]]:
    """Split chunks into batches that each fit under the LLM token budget.

    Each batch's estimated token count (chars / ~3.5) stays within
    ``budget_tokens`` so a full-paper summary is produced from every part
    of the paper, not just the beginning — and every individual map call
    stays under the provider's tokens-per-minute limit.
    """
    batches = []
    current: list[dict] = []
    current_tokens = 0
    for chunk in chunks:
        text = chunk.get("chunk_text", "")
        if not text:
            continue
        chunk_tokens = _estimate_tokens(text)
        if current and current_tokens + chunk_tokens + _HEADER_TOKEN_ALLOWANCE > budget_tokens:
            batches.append(current)
            current = []
            current_tokens = 0
        current.append(chunk)
        current_tokens += chunk_tokens
    if current:
        batches.append(current)
    return batches


def handle_summarize():
    body = require_json_body()

    paper_id = (body.get("paper_id") or "").strip()
    if not paper_id:
        raise AppError(
            message="Field 'paper_id' is required.",
            status_code=400,
            code="MISSING_PAPER_ID",
        )

    if not ObjectId.is_valid(paper_id):
        raise AppError(
            message=f"Invalid paper ID format: '{paper_id}'.",
            status_code=400,
            code="INVALID_ID",
        )

    force = body.get("force_regenerate", False)

    user_id = getattr(g, "user_id", None)
    paper = paper_model.get_paper(paper_id, user_id=user_id)
    if not paper:
        raise AppError(
            message=f"No paper found with ID '{paper_id}'.",
            status_code=404,
            code="PAPER_NOT_FOUND",
        )

    if not force and paper.get("summary"):
        return jsonify({
            "success": True,
            "data": {
                "summary": paper["summary"],
                "cached": True,
            },
        }), 200

    if paper.get("status") != "processed":
        raise AppError(
            message=f"Paper '{paper_id}' is not yet fully processed. Current status: {paper.get('status', 'unknown')}.",
            status_code=422,
            code="PAPER_NOT_PROCESSED",
        )

    chunks = chunk_model.get_chunks_by_paper(paper_id)
    if not chunks:
        raise AppError(
            message=f"No text content found for paper '{paper_id}'. The paper may be empty or scanned.",
            status_code=422,
            code="NO_CONTENT",
        )

    batches = _batch_chunks(chunks, _MAP_INPUT_TOKEN_BUDGET)
    if len(batches) == 1:
        context = "\n\n".join(c["chunk_text"] for c in batches[0])
        summary = gemini_service.generate_summary(context)
    else:
        partials = []
        for i, batch in enumerate(batches):
            if i > 0:
                # Pace sequential map calls so requests stay within the
                # per-minute RPM window; token count also accounted for.
                per_call_tokens = (
                    min(
                        sum(_estimate_tokens(c["chunk_text"]) for c in batch),
                        _MAP_INPUT_TOKEN_BUDGET,
                    )
                    + _OUTPUT_TOKEN_ALLOWANCE
                    + _TEMPLATE_OVERHEAD_TOKENS
                )
                delay = max(
                    _MIN_BATCH_DELAY_SECONDS,
                    per_call_tokens * 60.0 / _TPM_LIMIT,
                )
                time.sleep(delay)
            context = "\n\n".join(c["chunk_text"] for c in batch)
            partials.append(gemini_service.generate_summary(context))
        summary = gemini_service.merge_summaries(partials)
    paper_model.update_paper(paper_id, {"summary": summary, "summaryModel": settings.GEMINI_MODEL_NAME})

    return jsonify({
        "success": True,
        "data": {
            "summary": summary,
            "cached": False,
        },
    }), 200
