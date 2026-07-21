import pytest
from backend.services.embedding_service import (
    generate_embedding,
    generate_embeddings_batch,
)
from backend.middlewares.error_handler import AppError


class TestGenerateEmbedding:
    def test_returns_fixed_dimension_vector(self):
        vec = generate_embedding("This is a test sentence.")
        assert isinstance(vec, list)
        assert len(vec) == 384

    def test_returns_different_vector_for_different_text(self):
        v1 = generate_embedding("Machine learning is interesting.")
        v2 = generate_embedding("I like to cook pasta.")
        assert v1 != v2

    def test_returns_similar_vectors_for_similar_text(self):
        v1 = generate_embedding("Neural networks for image classification.")
        v2 = generate_embedding("Deep learning for image recognition.")
        v3 = generate_embedding("The stock market crashed today.")

        sim_12 = sum(a * b for a, b in zip(v1, v2))
        sim_13 = sum(a * b for a, b in zip(v1, v3))
        assert sim_12 > sim_13

    def test_raises_error_for_empty_string(self):
        with pytest.raises(AppError) as exc:
            generate_embedding("")
        assert exc.value.code == "EMPTY_TEXT"

    def test_raises_error_for_whitespace_only(self):
        with pytest.raises(AppError) as exc:
            generate_embedding("   \n  ")
        assert exc.value.code == "EMPTY_TEXT"


class TestGenerateEmbeddingsBatch:
    def test_returns_embeddings_for_multiple_texts(self):
        texts = ["First text.", "Second text.", "Third text."]
        vectors = generate_embeddings_batch(texts)
        assert len(vectors) == 3
        assert all(len(v) == 384 for v in vectors)

    def test_raises_error_for_empty_list(self):
        with pytest.raises(AppError) as exc:
            generate_embeddings_batch([])
        assert exc.value.code == "EMPTY_BATCH"
