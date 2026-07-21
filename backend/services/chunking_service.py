import re
from backend.config.settings import settings
from backend.utils.logger import logger


def _estimate_tokens(text: str) -> int:
    """Roughly estimate the number of tokens in a text string.

    Uses a ~4 characters per token heuristic, which is a reasonable
    approximation for English text.
    """
    return len(text) // 4


def _split_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs, preserving paragraph order."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences on sentence-ending punctuation."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _split_oversized_paragraph(
    paragraphs: list[str], chunk_tokens: int
) -> list[str]:
    """Break any paragraph that exceeds chunk_size into sentence groups.

    Falls back to character-boundary splitting for text without
    sentence punctuation.
    """
    result = []
    for para in paragraphs:
        if _estimate_tokens(para) <= chunk_tokens:
            result.append(para)
            continue

        sentences = _split_sentences(para)
        if len(sentences) == 1:
            max_chars = chunk_tokens * 4
            for i in range(0, len(para), max_chars):
                result.append(para[i : i + max_chars].strip())
            continue

        group = []
        group_tokens = 0
        for sent in sentences:
            sent_tokens = _estimate_tokens(sent)
            if group_tokens + sent_tokens > chunk_tokens and group:
                result.append(" ".join(group))
                group = []
                group_tokens = 0
            group.append(sent)
            group_tokens += sent_tokens
        if group:
            result.append(" ".join(group))
    return result


def clean_text(text: str) -> str:
    """Normalize whitespace and remove common PDF extraction artifacts.

    Args:
        text: Raw extracted text from a PDF.

    Returns:
        Cleaned text with normalized whitespace.
    """
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\n){3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[dict]:
    """Split cleaned text into overlapping, semantically coherent chunks.

    Chunking respects paragraph boundaries where possible: paragraphs
    are accumulated until the chunk_size token estimate is reached,
    then finalized. Overlap is achieved by rewinding
    approximately *overlap* tokens from the end of the previous chunk.

    Args:
        text: Cleaned text to chunk.
        chunk_size: Target chunk size in tokens (default from settings).
        overlap: Number of tokens of overlap between consecutive chunks.

    Returns:
        A list of dicts, each containing:
            - text (str): The chunk text.
            - chunk_index (int): Zero-indexed position.

    Raises:
        ValueError: If text is empty after cleaning.
    """
    chunk_size = chunk_size or settings.DEFAULT_CHUNK_SIZE
    overlap = overlap or settings.DEFAULT_CHUNK_OVERLAP

    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Cannot chunk empty text.")

    paragraphs = _split_into_paragraphs(cleaned)
    paragraphs = _split_oversized_paragraph(paragraphs, chunk_size)
    chunks = []
    current_chunk = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _estimate_tokens(para)

        if para_tokens > chunk_size:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            chunks.append(para)
            continue

        if current_tokens + para_tokens > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            overlap_text = _get_overlap_text(current_chunk, overlap)
            current_chunk = [overlap_text] if overlap_text else []
            current_tokens = _estimate_tokens(overlap_text) if overlap_text else 0

        current_chunk.append(para)
        current_tokens += para_tokens

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return [
        {"text": chunk, "chunk_index": i}
        for i, chunk in enumerate(chunks)
    ]


def _get_overlap_text(paragraphs: list[str], overlap_tokens: int) -> str:
    """Extract trailing text from a list of paragraphs for overlap."""
    combined = "\n\n".join(paragraphs)
    if _estimate_tokens(combined) <= overlap_tokens:
        return ""

    target_chars = overlap_tokens * 4
    if target_chars >= len(combined):
        return ""

    return combined[-target_chars:].lstrip()


def chunk_paper(
    pages: list[dict],
    chunk_size: int = None,
    overlap: int = None,
) -> list[dict]:
    """Run the full chunking pipeline on a paper's extracted pages.

    Args:
        pages: Output from pdf_service.process_pdf — list of
               {page_number, text} dicts.
        chunk_size: Target chunk size in tokens.
        overlap: Token overlap between chunks.

    Returns:
        A list of chunk dicts, each containing:
            - text (str): The chunk text.
            - chunk_index (int): Zero-indexed position.
            - page_number (int): Approximate source page.

    Raises:
        ValueError: If pages list is empty.
    """
    if not pages:
        raise ValueError("Cannot chunk a paper with no pages.")

    full_text = "\n\n".join(p["text"] for p in pages)
    chunks = chunk_text(full_text, chunk_size, overlap)

    char_positions = []
    pos = 0
    for page in pages:
        char_positions.append((pos, pos + len(page["text"])))
        pos += len(page["text"]) + 2

    for chunk in chunks:
        start_idx = full_text.find(chunk["text"])
        for i, (page_start, page_end) in enumerate(char_positions):
            if page_start <= start_idx < page_end:
                chunk["page_number"] = i + 1
                break
        else:
            chunk["page_number"] = 1

    logger.info(
        f"Chunked paper into {len(chunks)} chunks "
        f"(size={chunk_size}, overlap={overlap})"
    )
    return chunks
