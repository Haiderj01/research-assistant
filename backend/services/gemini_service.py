import time
from google import genai
from backend.config import settings
from backend.middlewares.error_handler import AppError
from backend.utils.logger import logger
from backend.services.groq_service import _load_prompt

_MAX_ATTEMPTS = 3
_MAX_OUTPUT_TOKENS = 8192


def _get_client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise AppError(
            message="Gemini API key is not configured.",
            status_code=500,
            code="MISSING_API_KEY",
        )
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _is_retryable(error_msg: str) -> bool:
    return (
        "429" in error_msg
        or "RATE_LIMIT" in error_msg
        or "503" in error_msg
        or "UNAVAILABLE" in error_msg
    )


def _generate(prompt: str, system_instruction: str | None = None) -> str:
    client = _get_client()
    model_name = settings.GEMINI_MODEL_NAME

    last_error = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            interaction = client.interactions.create(
                model=model_name,
                input=prompt,
                system_instruction=system_instruction,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": _MAX_OUTPUT_TOKENS,
                },
            )
            text = interaction.output_text
            if not text:
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = 2 ** attempt * 5
                    logger.warning(
                        f"Gemini empty response, retrying in {delay:.0f}s "
                        f"(attempt {attempt + 1}/{_MAX_ATTEMPTS})"
                    )
                    time.sleep(delay)
                    continue
                raise AppError(
                    message="Gemini returned an empty response.",
                    status_code=502,
                    code="EMPTY_RESPONSE",
                )
            return text.strip()
        except AppError:
            raise
        except Exception as e:
            last_error = e
            error_str = str(e)
            if not _is_retryable(error_str) or attempt == _MAX_ATTEMPTS - 1:
                break
            delay = 2 ** attempt * 5
            logger.warning(
                f"Gemini transient error, retrying in {delay:.0f}s "
                f"(attempt {attempt + 1}/{_MAX_ATTEMPTS})"
            )
            time.sleep(delay)

    logger.exception("Gemini API call failed")
    msg = str(last_error) if settings.DEBUG_MODE else (
        "The AI generation service is temporarily unavailable. Please try again."
    )
    raise AppError(
        message=msg,
        status_code=502,
        code="GROQ_ERROR",
    )


def generate_summary(context: str) -> str:
    """Generate a structured summary of a paper whose text fits one call."""
    system = _load_prompt("system.txt")
    template = _load_prompt("summary.txt")
    prompt = template.replace("{context}", context)
    logger.info("Generating summary via Gemini")
    return _generate(prompt, system_instruction=system)


def merge_summaries(partials: list[str]) -> str:
    """Merge per-batch partial summaries into a single full summary."""
    system = _load_prompt("system.txt")
    template = _load_prompt("summary_merge.txt")
    parts = "\n\n".join(f"--- Part {i + 1} ---\n{p}" for i, p in enumerate(partials))
    prompt = template.replace("{parts}", parts)
    logger.info(f"Merging {len(partials)} partial summaries via Gemini")
    return _generate(prompt, system_instruction=system)
