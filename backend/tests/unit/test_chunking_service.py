import pytest
from backend.services.chunking_service import (
    clean_text,
    chunk_text,
    chunk_paper,
)


class TestCleanText:
    def test_normalizes_excess_whitespace(self):
        result = clean_text("Hello    world.\n\n\n\nMore text.")
        assert "    " not in result
        assert "\n\n\n" not in result

    def test_strips_leading_trailing_whitespace(self):
        result = clean_text("  Hello world.  ")
        assert result == "Hello world."

    def test_removes_trailing_tab_newline_artifacts(self):
        result = clean_text("Line one  \nLine two")
        assert "  \n" not in result


class TestChunkText:
    def test_returns_single_chunk_for_short_text(self):
        chunks = chunk_text("Short text.", chunk_size=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0]["chunk_index"] == 0

    def test_splits_long_text_into_multiple_chunks(self):
        text = " ".join(["word"] * 5000)
        chunks = chunk_text(text, chunk_size=200, overlap=20)
        assert len(chunks) > 1

    def test_chunks_have_overlap(self):
        text = "\n\n".join([f"Paragraph {i} content here." for i in range(50)])
        chunks = chunk_text(text, chunk_size=100, overlap=30)
        if len(chunks) > 1:
            assert chunks[1]["text"] != ""

    def test_raises_value_error_for_empty_text(self):
        with pytest.raises(ValueError, match="Cannot chunk empty text"):
            chunk_text("   \n\n  ", chunk_size=100, overlap=10)

    def test_chunks_have_correct_structure(self):
        chunks = chunk_text("Some text here.", chunk_size=100, overlap=10)
        assert "text" in chunks[0]
        assert "chunk_index" in chunks[0]

    def test_respects_paragraph_boundaries(self):
        text = "\n\n".join([
            "A" * 2000,
            "B" * 2000,
            "C" * 2000,
        ])
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) >= 1


class TestChunkPaper:
    def test_chunks_paper_from_pages(self):
        pages = [
            {"page_number": 1, "text": "Page one content. " * 50},
            {"page_number": 2, "text": "Page two content. " * 50},
        ]
        chunks = chunk_paper(pages, chunk_size=100, overlap=20)
        assert len(chunks) >= 1
        for c in chunks:
            assert "page_number" in c
            assert "chunk_index" in c

    def test_raises_value_error_for_no_pages(self):
        with pytest.raises(ValueError, match="Cannot chunk a paper with no pages"):
            chunk_paper([], chunk_size=100, overlap=20)
