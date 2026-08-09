import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bson import ObjectId
from backend.middlewares.error_handler import AppError
from backend.models import paper_model, chunk_model
from backend.services import embedding_service, groq_service
from backend.services.vector_store_service import vector_store
from backend.config import settings
from backend.utils.logger import logger

GAP_RETRIEVAL_QUERY = (
    "limitations, challenges, weaknesses, and future work of this study"
)
PER_PAPER_CHUNKS = 5
MIN_PAPERS = 2
MAX_PAPERS = 12


def _validate_paper_ids(paper_ids) -> list[str]:
    """Validate the paper_ids payload shape and cardinality.

    Args:
        paper_ids: Raw value from the request body.

    Returns:
        The validated list of paper ID strings.

    Raises:
        AppError: 400 if the payload is malformed or the cardinality is
        outside the allowed range, or if any ID is not a valid ObjectId.
    """
    if not paper_ids or not isinstance(paper_ids, list) or not paper_ids:
        raise AppError(
            message="Field 'paper_ids' must be a non-empty array of paper IDs.",
            status_code=400,
            code="MISSING_PAPER_IDS",
        )
    if len(paper_ids) < MIN_PAPERS:
        raise AppError(
            message=f"At least {MIN_PAPERS} paper IDs are required for gap analysis.",
            status_code=400,
            code="INSUFFICIENT_PAPERS",
        )
    if len(paper_ids) > MAX_PAPERS:
        raise AppError(
            message=f"At most {MAX_PAPERS} papers can be analyzed at once. "
                    f"Please narrow your selection.",
            status_code=400,
            code="TOO_MANY_PAPERS",
        )

    invalid_ids = [pid for pid in paper_ids if not ObjectId.is_valid(pid)]
    if invalid_ids:
        raise AppError(
            message=f"Invalid paper ID format: {invalid_ids}.",
            status_code=400,
            code="INVALID_IDS",
        )
    return paper_ids


def _verify_papers(paper_ids: list[str], user_id: str) -> list[dict]:
    """Load and verify ownership/processing status for every paper.

    Args:
        paper_ids: Validated paper ID strings.
        user_id: The authenticated user's ID.

    Returns:
        The ordered list of paper documents.

    Raises:
        AppError: 404 if a paper is missing or owned by another user; 422
        if a paper is not yet fully processed.
    """
    papers = []
    for pid in paper_ids:
        paper = paper_model.get_paper(pid, user_id=user_id)
        if not paper:
            raise AppError(
                message=f"No paper found with ID '{pid}'.",
                status_code=404,
                code="PAPER_NOT_FOUND",
            )
        if paper.get("status") != "processed":
            raise AppError(
                message=f"Paper '{pid}' is not yet fully processed. Current status: {paper.get('status', 'unknown')}.",
                status_code=422,
                code="PAPER_NOT_PROCESSED",
            )
        papers.append(paper)
    return papers


def _retrieve_paper_chunks(paper_id: str, top_k: int, query_vector: list[float]) -> str:
    """Retrieve the most relevant limitation/future-work chunks for a paper.

    Args:
        paper_id: The paper ID to scope retrieval to.
        top_k: Number of chunks to return.
        query_vector: Precomputed embedding for the retrieval query.

    Returns:
        The joined chunk text, or an empty string if nothing was found.
    """
    results = vector_store.search(query_vector, k=top_k, paper_ids=[paper_id])
    if not results:
        return ""

    vector_ids = [r["chunk_id"] for r in results]
    chunks = chunk_model.get_chunks_by_vector_ids(vector_ids)
    chunks_by_id = {c["vector_id"]: c for c in (chunks or [])}

    parts = []
    for r in results:
        chunk = chunks_by_id.get(r["chunk_id"])
        if chunk:
            parts.append(chunk["chunk_text"])
    return "\n\n".join(parts)


def _parse_gap_blocks(text: str) -> list[dict]:
    """Parse the reduce-step LLM output into structured gap dicts.

    Args:
        text: The raw LLM gap-analysis text in the agreed plain-text format.

    Returns:
        A list of dicts with keys description, supporting_papers, strength,
        and suggested_direction.
    """
    blocks = re.split(r"\n\s*\n", text.strip())
    gaps = []
    for block in blocks:
        if not block.strip():
            continue
        description = _extract_field(block, "Gap:")
        supporting = _extract_field(block, "Supporting Papers:")
        strength = _extract_field(block, "Strength:")
        direction = _extract_field(block, "Suggested Direction:")
        if not description or not supporting:
            continue
        paper_ids = [
            pid.strip()
            for pid in supporting.split(",")
            if pid.strip() and ObjectId.is_valid(pid.strip())
        ]
        if not paper_ids:
            continue
        gaps.append({
            "description": description,
            "supporting_papers": paper_ids,
            "strength": "multiple" if strength.lower().strip() == "multiple" else "single",
            "suggested_direction": direction,
        })
    return gaps


def _extract_field(block: str, label: str) -> str:
    """Extract a label: value pair from a parsed block.

    Args:
        block: A single gap block.
        label: The plain-text label (e.g., "Gap:").

    Returns:
        The trimmed value on the label's line, or an empty string.
    """
    match = re.search(re.escape(label) + r"\s+([^\n]+)", block)
    if not match:
        return ""
    return match.group(1).strip()


def analyze_research_gaps(paper_ids, user_id: str) -> dict:
    """Run the full research gap analysis over a set of papers.

    Map step: for each paper, retrieve its limitation/future-work chunks and
    ask the LLM to extract a structured per-paper summary. Reduce step: send
    all per-paper summaries together and ask the LLM to synthesize cross-paper
    gaps, each traceable to the papers that stated it.

    Args:
        paper_ids: Paper IDs to analyze (2-12).
        user_id: The authenticated user's ID.

    Returns:
        A dict with:
            - gaps: list of {description, supporting_papers, strength,
              suggested_direction}.
            - per_paper_summaries: list of {paper_id, title, summary}.

    Raises:
        AppError: 400 on invalid input, 404 on missing/foreign papers, 422
        on unprocessed papers, 502 if any LLM call fails.
    """
    paper_ids = _validate_paper_ids(paper_ids)
    papers = _verify_papers(paper_ids, user_id)
    papers_by_id = {str(p["_id"]): p for p in papers}

    started = time.time()

    query_vector = embedding_service.generate_embedding(GAP_RETRIEVAL_QUERY)
    contexts = [
        _retrieve_paper_chunks(
            str(paper["_id"]), PER_PAPER_CHUNKS, query_vector
        )
        for paper in papers
    ]

    def _extract(idx: int) -> dict:
        paper = papers[idx]
        context = contexts[idx]
        try:
            if context:
                summary = groq_service.extract_paper_gaps(context)
            else:
                summary = (
                    "None stated: no content could be retrieved for this paper "
                    "related to limitations or future work."
                )
        except AppError:
            logger.error(f"Gap analysis map step failed for paper {paper['_id']}")
            raise
        except Exception as exc:
            logger.exception(f"Gap analysis map step failed for paper {paper['_id']}")
            raise AppError(
                message="The AI generation service failed while analyzing one of the papers. Please try again.",
                status_code=502,
                code="GROQ_ERROR",
            ) from exc
        return {
            "paper_id": str(paper["_id"]),
            "title": paper.get("title", ""),
            "summary": summary,
        }

    per_paper_summaries = [None] * len(papers)
    max_workers = min(len(papers), settings.GAP_MAP_CONCURRENCY)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {executor.submit(_extract, i): i for i in range(len(papers))}
        for future in as_completed(future_to_idx):
            per_paper_summaries[future_to_idx[future]] = future.result()

    summaries_blob = "\n\n".join(
        f"--- Paper ID: {s['paper_id']} | Title: {s['title']} ---\n{s['summary']}"
        for s in per_paper_summaries
    )

    try:
        analysis_text = groq_service.synthesize_research_gaps(summaries_blob)
    except AppError:
        logger.error("Gap analysis reduce step failed")
        raise
    except Exception as exc:
        logger.exception("Gap analysis reduce step failed")
        raise AppError(
            message="The AI generation service failed while synthesizing research gaps. Please try again.",
            status_code=502,
            code="GROQ_ERROR",
        ) from exc

    gaps = _parse_gap_blocks(analysis_text)

    elapsed = time.time() - started
    logger.info(
        f"Gap analysis completed for {len(paper_ids)} papers "
        f"({len(gaps)} gaps, {elapsed:.2f}s)"
    )

    return {
        "gaps": gaps,
        "per_paper_summaries": per_paper_summaries,
    }
