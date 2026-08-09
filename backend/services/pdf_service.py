import fitz
from backend.config import settings
from backend.middlewares.error_handler import AppError
from backend.utils.logger import logger


def validate_pdf(file_path: str) -> bool:
    """Validate that a file is a well-formed PDF with extractable content.

    Args:
        file_path: Absolute or relative path to the file.

    Returns:
        True if the file is valid.

    Raises:
        AppError: If the file is not a valid PDF or cannot be opened.
    """
    try:
        doc = fitz.open(file_path)
        doc.close()
        return True
    except fitz.FileDataError:
        raise AppError(
            message="The file is corrupted or not a valid PDF.",
            status_code=422,
            code="INVALID_PDF",
        )


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """Extract text content page by page from a PDF file.

    Args:
        file_path: Path to a valid PDF file.

    Returns:
        A list of dicts, one per page, each containing:
            - page_number (int): 1-indexed page number.
            - text (str): Extracted text content.

    Raises:
        AppError: If extraction fails unexpectedly.
    """
    try:
        doc = fitz.open(file_path)
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text().strip()
            pages.append({"page_number": i, "text": text})
        doc.close()
        return pages
    except Exception:
        logger.exception("Unexpected error during PDF text extraction")
        raise AppError(
            message="An unexpected error occurred while extracting text from the PDF.",
            status_code=500,
            code="EXTRACTION_FAILED",
        )


def detect_scanned_pdf(pages: list[dict], min_chars: int = 100) -> bool:
    """Check whether a PDF appears to be a scanned image with no extractable text.

    Args:
        pages: Output from extract_text_from_pdf.
        min_chars: Minimum total characters across all pages to consider the PDF
                   as having extractable text.

    Returns:
        True if the PDF appears to be scanned/image-based.
    """
    total_chars = sum(len(p["text"]) for p in pages)
    return total_chars < min_chars


def process_pdf(file_path: str) -> dict:
    """Run the full PDF processing pipeline: validate, extract, scan detect.

    Args:
        file_path: Path to a PDF file.

    Returns:
        A dict containing:
            - pages (list[dict]): Extracted page data.
            - total_pages (int): Number of pages.
            - total_chars (int): Total characters extracted.

    Raises:
        AppError: If the PDF is invalid, corrupted, or has no extractable text.
    """
    logger.info(f"Processing PDF: {file_path}")

    validate_pdf(file_path)
    pages = extract_text_from_pdf(file_path)

    if detect_scanned_pdf(pages):
        raise AppError(
            message="This PDF appears to be a scanned document with no extractable text. "
                    "OCR is not supported in the current version.",
            status_code=422,
            code="SCANNED_PDF",
        )

    total_chars = sum(len(p["text"]) for p in pages)
    logger.info(f"PDF processed: {len(pages)} pages, {total_chars} characters")

    return {
        "pages": pages,
        "total_pages": len(pages),
        "total_chars": total_chars,
    }
