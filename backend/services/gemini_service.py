import os
import re
import time
from google import genai
from google.genai import types
from backend.config.settings import settings
from backend.middlewares.error_handler import AppError
from backend.utils.logger import logger

_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _load_prompt(name: str) -> str:
    path = os.path.join(_PROMPT_DIR, name)
    with open(path) as f:
        return f.read().strip()


def _get_client() -> genai.Client:
    api_key = settings.GEMINI_API_KEY

    if not api_key:
        raise AppError(
            message="Gemini API key is not configured.",
            status_code=500,
            code="MISSING_API_KEY",
        )

    return genai.Client(api_key=api_key)


def _extract_retry_delay(error_msg: str) -> float:
    match = re.search(r"retry in ([\d.]+)s", error_msg)
    return float(match.group(1)) if match else 0


def _generate(prompt: str, system_instruction: str | None = None) -> str:
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=2048,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    last_error = None
    for attempt in range(3):
        try:
            model_name = settings.GEMINI_MODEL_NAME

            if not model_name:
                raise AppError(
                    message="Gemini model name is not configured.",
                    status_code=500,
                    code="MISSING_MODEL_NAME",
                )

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )

            if response.text is None:
                raise AppError(
                    message="Gemini returned an empty response.",
                    status_code=502,
                    code="EMPTY_GEMINI_RESPONSE",
                )

            return response.text.strip()
        except Exception as e:
            last_error = e
            error_str = str(e)
            is_quota = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str
            if not is_quota or attempt == 2:
                break
            delay = _extract_retry_delay(error_str) or (2 ** attempt * 5)
            logger.warning(f"Gemini quota exhausted, retrying in {delay:.0f}s (attempt {attempt + 1}/3)")
            time.sleep(delay)

    logger.exception("Gemini API call failed")
    msg = str(last_error) if settings.DEBUG_MODE else "The AI generation service is temporarily unavailable. Please try again."
    raise AppError(
        message=msg,
        status_code=502,
        code="GEMINI_ERROR",
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
    logger.info("Generating answer via Gemini")
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
    logger.info("Generating summary via Gemini")
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
    logger.info("Extracting per-paper limitations and future work via Gemini")
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
    logger.info("Synthesizing cross-paper research gaps via Gemini")
    return _generate(prompt, system_instruction=system)
