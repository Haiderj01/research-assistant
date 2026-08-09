import threading
from sentence_transformers import SentenceTransformer
from backend.config import settings
from backend.middlewares.error_handler import AppError
from backend.utils.logger import logger

_model = None
_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """Lazy-load the Sentence Transformer embedding model.

    Thread-safe: uses a lock so the model is loaded exactly once
    even when multiple background threads call this simultaneously.

    Returns:
        The loaded SentenceTransformer model.
    """
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
                _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                logger.info("Embedding model loaded successfully.")
    return _model


def preload_model():
    """Pre-load the embedding model at server startup.

    Call during application initialization so the model is ready
    before background threads need it.
    """
    _get_model()


def generate_embedding(text: str) -> list[float]:
    """Generate a single vector embedding for a text string.

    Args:
        text: The input text to embed.

    Returns:
        A list of floats representing the embedding vector.

    Raises:
        AppError: If the input text is empty.
    """
    if not text or not text.strip():
        raise AppError(
            message="Cannot generate embedding for empty text.",
            status_code=422,
            code="EMPTY_TEXT",
        )

    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    logger.debug(f"Generated embedding (dim={len(vector)})")
    return vector.tolist()


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of text strings.

    Batched embedding is more efficient than calling
    generate_embedding repeatedly, as the underlying model
    processes inputs in parallel where supported.

    Args:
        texts: A list of text strings to embed.

    Returns:
        A list of embedding vectors (each a list of floats),
        in the same order as the input texts.

    Raises:
        AppError: If the input list is empty.
    """
    if not texts:
        raise AppError(
            message="Cannot generate embeddings for an empty list.",
            status_code=422,
            code="EMPTY_BATCH",
        )

    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    logger.debug(f"Generated {len(vectors)} embeddings in batch")
    return [v.tolist() for v in vectors]
