import os
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
    if not settings.GEMINI_API_KEY:
        raise AppError(
            message="Gemini API key is not configured.",
            status_code=500,
            code="MISSING_API_KEY",
        )
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _generate(prompt: str, system_instruction: str = None) -> str:
    client = _get_client()
    config = types.GenerateContentConfig(
        temperature=0.3,
        max_output_tokens=2048,
    )
    if system_instruction:
        config.system_instruction = system_instruction

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL_NAME,
            contents=prompt,
            config=config,
        )
        return response.text.strip()
    except Exception as e:
        logger.exception("Gemini API call failed")
        msg = str(e) if settings.DEBUG_MODE else "The AI generation service is temporarily unavailable. Please try again."
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
