import os
import tempfile
import fitz
import pytest
from backend.services.pdf_service import (
    validate_pdf,
    extract_text_from_pdf,
    detect_scanned_pdf,
    process_pdf,
)
from backend.middlewares.error_handler import AppError


def _create_sample_pdf(text: str = "Hello world. This is a test paper.") -> str:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(72, 72), text)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc.save(tmp.name)
    doc.close()
    return tmp.name


def _create_empty_pdf() -> str:
    doc = fitz.open()
    doc.new_page()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc.save(tmp.name)
    doc.close()
    return tmp.name


class TestValidatePdf:
    def test_valid_pdf_returns_true(self):
        path = _create_sample_pdf()
        assert validate_pdf(path) is True
        os.unlink(path)

    def test_invalid_file_raises_error(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(b"not a pdf")
            f.flush()
            with pytest.raises(AppError) as exc:
                validate_pdf(f.name)
            assert exc.value.status_code == 422
            assert exc.value.code == "INVALID_PDF"


class TestExtractTextFromPdf:
    def test_extracts_text_from_single_page(self):
        path = _create_sample_pdf("Research paper content here.")
        pages = extract_text_from_pdf(path)
        assert len(pages) == 1
        assert "Research paper content here." in pages[0]["text"]
        assert pages[0]["page_number"] == 1
        os.unlink(path)

    def test_extracts_text_from_multi_page(self):
        doc = fitz.open()
        doc.new_page()
        doc.new_page()
        doc[-1].insert_text(fitz.Point(72, 72), "Page two content")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc.save(tmp.name)
        doc.close()
        pages = extract_text_from_pdf(tmp.name)
        assert len(pages) == 2
        assert "Page two content" in pages[1]["text"]
        os.unlink(tmp.name)


class TestDetectScannedPdf:
    def test_returns_true_for_empty_text(self):
        pages = [{"page_number": 1, "text": ""}]
        assert detect_scanned_pdf(pages) is True

    def test_returns_false_for_substantial_text(self):
        pages = [{"page_number": 1, "text": "A" * 500}]
        assert detect_scanned_pdf(pages) is False


class TestProcessPdf:
    def test_processes_valid_pdf_successfully(self):
        path = _create_sample_pdf(
            "This is a test paper with enough content to pass the scan detection threshold. "
            "It contains multiple sentences that simulate a real research paper abstract. "
            "The system should process this without raising a scanned PDF error."
        )
        result = process_pdf(path)
        assert result["total_pages"] == 1
        assert result["total_chars"] > 0
        assert len(result["pages"]) == 1
        os.unlink(path)

    def test_raises_error_for_empty_pdf(self):
        path = _create_empty_pdf()
        with pytest.raises(AppError) as exc:
            process_pdf(path)
        assert exc.value.code == "SCANNED_PDF"
        os.unlink(path)
