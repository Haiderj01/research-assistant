import os
import tempfile
import pytest
from backend.services.vector_store_service import VectorStoreService
from backend.middlewares.error_handler import AppError


@pytest.fixture
def store():
    tmp_dir = tempfile.mkdtemp()
    vs = VectorStoreService(
        index_path=os.path.join(tmp_dir, "test.faiss"),
        mapping_path=os.path.join(tmp_dir, "test_mapping.json"),
        vectors_path=os.path.join(tmp_dir, "test_vectors.npy"),
    )
    yield vs


def _random_vector(dim=384):
    import random
    vec = [random.uniform(-1, 1) for _ in range(dim)]
    norm = sum(x * x for x in vec) ** 0.5
    return [x / norm for x in vec]


class TestVectorStoreService:
    def test_add_vectors_increases_size(self, store):
        vectors = [_random_vector() for _ in range(3)]
        ids = store.add_vectors(vectors, ["a", "b", "c"])
        assert store.size == 3
        assert len(ids) == 3

    def test_search_returns_top_k_results(self, store):
        vectors = [_random_vector() for _ in range(10)]
        store.add_vectors(vectors, [f"chunk_{i}" for i in range(10)])
        query = _random_vector()
        results = store.search(query, k=3)
        assert len(results) == 3
        assert all("chunk_id" in r for r in results)
        assert all("score" in r for r in results)
        assert results[0]["position"] == 0

    def test_search_on_empty_index_returns_empty_list(self, store):
        query = _random_vector()
        results = store.search(query, k=5)
        assert results == []

    def test_remove_vectors_decreases_size(self, store):
        vectors = [_random_vector() for _ in range(5)]
        store.add_vectors(vectors, [f"chunk_{i}" for i in range(5)])
        assert store.size == 5
        removed = store.remove_vectors(["chunk_0", "chunk_2"])
        assert removed == 2
        assert store.size == 3

    def test_remove_nonexistent_returns_zero(self, store):
        vectors = [_random_vector() for _ in range(3)]
        store.add_vectors(vectors, ["a", "b", "c"])
        removed = store.remove_vectors(["nonexistent"])
        assert removed == 0
        assert store.size == 3

    def test_mismatched_vectors_and_ids_raises_error(self, store):
        vectors = [_random_vector() for _ in range(3)]
        with pytest.raises(AppError, match="must match"):
            store.add_vectors(vectors, ["only_one_id"])

    def test_empty_batch_raises_error(self, store):
        with pytest.raises(AppError, match="empty batch"):
            store.add_vectors([], [])

    def test_dimension_mismatch_raises_error(self, store):
        with pytest.raises(AppError, match="dimension"):
            store.add_vectors([[1.0, 2.0, 3.0]], ["bad_dim"])

    def test_persistence_survives_reload(self, store):
        vectors = [_random_vector() for _ in range(4)]
        store.add_vectors(vectors, ["w", "x", "y", "z"])
        old_size = store.size

        vs2 = VectorStoreService(
            index_path=store._index_path,
            mapping_path=store._mapping_path,
            vectors_path=store._vectors_path,
        )
        assert vs2.size == old_size
        query = _random_vector()
        results = vs2.search(query, k=2)
        assert len(results) == 2

    def test_returns_most_similar_vector_first(self, store):
        vec_a = _random_vector()
        vec_b = _random_vector()
        query = vec_a[:]
        store.add_vectors([vec_a, vec_b], ["target", "distract"])
        results = store.search(query, k=2)
        assert results[0]["chunk_id"] == "target"
