import os
import re
import time
from groq import Groq
from backend.config import settings
from backend.middlewares.error_handler import AppError
from backend.utils.logger import logger

_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")

_MAX_RETRY_DELAY_SECONDS = 60
_MAX_ATTEMPTS = 3


def _load_prompt(name: str) -> str:
    path = os.path.join(_PROMPT_DIR, name)
    with open(path) as f:
        return f.read().strip()


def _get_client() -> Groq:
    api_key = settings.GROQ_API_KEY

    if not api_key:
        raise AppError(
            message="LLM API key is not configured.",
            status_code=500,
            code="MISSING_API_KEY",
        )

    return Groq(api_key=api_key)


def _extract_retry_delay(exc: Exception) -> float:
    """Return the server-suggested retry delay in seconds, if any."""
    msg = str(exc)
    match = re.search(r"retry (?:in|after) ([\d.]+)", msg)
    if match:
        return float(match.group(1))

    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers:
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
    return 0


def _is_retryable(error_msg: str) -> bool:
    """Return True if the LLM error is transient and worth retrying.

    Retries quota/rate-limit exhaustion (429 / RATE_LIMIT) and transient
    model-unavailability errors (503 / UNAVAILABLE), which signal high
    demand that typically subsides within seconds.
    """
    return (
        "429" in error_msg
        or "RATE_LIMIT" in error_msg
        or "503" in error_msg
        or "UNAVAILABLE" in error_msg
    )


def _generate(prompt: str, system_instruction: str | None = None) -> str:
    client = _get_client()
    model_name = settings.GROQ_MODEL_NAME

    if not model_name:
        raise AppError(
            message="LLM model name is not configured.",
            status_code=500,
            code="MISSING_MODEL_NAME",
        )

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})

    user_content = prompt
    if len(prompt) > settings.MAX_LLM_INPUT_CHARS:
        user_content = prompt[: settings.MAX_LLM_INPUT_CHARS]
        logger.warning(
            f"Truncating LLM prompt from {len(prompt)} to "
            f"{len(user_content)} chars to fit the model's token limit"
        )
    messages.append({"role": "user", "content": user_content})

    last_error = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )

            content = response.choices[0].message.content
            if not content:
                raise AppError(
                    message="LLM returned an empty response.",
                    status_code=502,
                    code="EMPTY_GROQ_RESPONSE",
                )

            return content.strip()
        except Exception as e:
            last_error = e
            error_str = str(e)
            if not _is_retryable(error_str) or attempt == _MAX_ATTEMPTS - 1:
                break
            suggested = _extract_retry_delay(e)
            if suggested > _MAX_RETRY_DELAY_SECONDS:
                logger.warning(
                    f"LLM rate limit with long reset ({suggested:.0f}s); "
                    "failing fast per quota limit."
                )
                break
            delay = suggested or (2 ** attempt * 5)
            logger.warning(
                f"LLM transient error, retrying in {delay:.0f}s (attempt {attempt + 1}/{_MAX_ATTEMPTS})"
            )
            time.sleep(delay)

    logger.exception("LLM API call failed")
    if "RATE_LIMIT" in str(last_error) or "429" in str(last_error):
        msg = (
            "The AI service has reached its rate or usage limit for now. "
            "Please wait a few minutes and try again."
        )
    else:
        msg = str(last_error) if settings.DEBUG_MODE else "The AI generation service is temporarily unavailable. Please try again."
    raise AppError(
        message=msg,
        status_code=502,
        code="GROQ_ERROR",
    )


def answer_question(context: str, question: str) -> str:
    """Generate an answer grounded in the provided context.

    Args:
        context: Retrieved paper chunks joined as text.
        question: The user's natural-language question.

    Returns:
        The generated answer text.
    """
    system = _load_prompt("system.txt")
    template = _load_prompt("qa.txt")
    prompt = template.replace("{context}", context).replace("{question}", question)
    logger.info("Generating answer via LLM")
    return _generate(prompt, system_instruction=system)


def generate_summary(context: str) -> str:
    """Generate a structured summary of a paper.

    Args:
        context: The paper's chunk text content.

    Returns:
        The generated summary text.
    """
    system = _load_prompt("system.txt")
    template = _load_prompt("summary.txt")
    prompt = template.replace("{context}", context)
    logger.info("Generating summary via LLM")
    return _generate(prompt, system_instruction=system)


def generate_comparison(context: str, dimensions: list[str]) -> str:
    """Generate a structured comparison across multiple papers.

    Args:
        context: Joined chunk text from all papers being compared.
        dimensions: List of comparison dimensions (e.g., dataset, method).

    Returns:
        The generated comparison text.
    """
    system = _load_prompt("system.txt")
    template = _load_prompt("comparison.txt")
    dims_str = ", ".join(dimensions)
    prompt = template.replace("{context}", context).replace("{dimensions}", dims_str)
    logger.info(f"Generating comparison across {len(dimensions)} dimensions")
    return _generate(prompt, system_instruction=system)


def merge_summaries(partials: list[str]) -> str:
    """Merge per-batch summaries of a paper into one complete summary.

    Args:
        partials: List of section-by-section summaries, one per chunk batch.

    Returns:
        A single structured summary covering the entire paper.
    """
    system = _load_prompt("system.txt")
    template = _load_prompt("summary_merge.txt")
    parts = "\n\n".join(f"--- Part {i + 1} ---\n{p}" for i, p in enumerate(partials))
    prompt = template.replace("{parts}", parts)
    logger.info(f"Merging {len(partials)} partial summaries into a full summary")
    return _generate(prompt, system_instruction=system)


def extract_paper_gaps(context: str) -> str:
    """Extract a single paper's stated limitations and future work.

    Args:
        context: The paper's retrieved chunk text.

    Returns:
        The generated structured summary of limitations and future work.
    """
    system = _load_prompt("system.txt")
    template = _load_prompt("gap_map.txt")
    prompt = template.replace("{context}", context)
    logger.info("Extracting per-paper limitations and future work via LLM")
    return _generate(prompt, system_instruction=system)


def synthesize_research_gaps(summaries: str) -> str:
    """Synthesize a cross-paper research gap analysis from per-paper summaries.

    Args:
        summaries: Joined per-paper limitation/future-work summaries, tagged
                   with paper IDs and titles.

    Returns:
        The generated gap analysis text.
    """
    system = _load_prompt("system.txt")
    template = _load_prompt("gap_reduce.txt")
    prompt = template.replace("{summaries}", summaries)
    logger.info("Synthesizing cross-paper research gaps via LLM")
    return _generate(prompt, system_instruction=system)
