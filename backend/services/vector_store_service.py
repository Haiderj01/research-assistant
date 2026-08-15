import json
import os
import threading
import numpy as np
import faiss
from backend.config import settings
from backend.middlewares.error_handler import AppError
from backend.models import chunk_model
from backend.utils.logger import logger


class VectorStoreService:
    """FAISS-based vector store with persistent ID mapping.

    Stores dense embedding vectors and supports similarity search.
    A sidecar mapping file links FAISS internal IDs to external
    chunk/document identifiers (e.g., MongoDB _id strings).
    """

    def __init__(self, index_path: str = None, mapping_path: str = None):
        self._index_path = index_path or os.path.join(
            settings.VECTOR_STORE_PATH, "index.faiss"
        )
        self._mapping_path = mapping_path or os.path.join(
            settings.VECTOR_STORE_PATH, "id_mapping.json"
        )
        self._next_id: int = 0
        self._id_to_chunk: dict[int, str] = {}
        self._index: faiss.Index = None
        self._lock: threading.Lock = threading.Lock()

        self._load_or_create()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_vectors(self, vectors: list[list[float]], chunk_ids: list[str]) -> list[int]:
        """Add vectors to the index with associated chunk IDs.

        Args:
            vectors: List of embedding vectors.
            chunk_ids: Corresponding chunk identifiers (MongoDB _id strings),
                       same length as vectors.

        Returns:
            List of FAISS internal IDs assigned to each vector.

        Raises:
            AppError: If lengths mismatch or vectors have wrong dimension.
        """
        if len(vectors) != len(chunk_ids):
            raise AppError(
                message="Number of vectors and chunk_ids must match.",
                status_code=422,
                code="MISMATCHED_INPUT",
            )
        if not vectors:
            raise AppError(
                message="Cannot add an empty batch of vectors.",
                status_code=422,
                code="EMPTY_BATCH",
            )

        dim = self._dimension()
        for v in vectors:
            if len(v) != dim:
                raise AppError(
                    message=f"Vector dimension {len(v)} does not match "
                            f"index dimension {dim}.",
                    status_code=422,
                    code="DIMENSION_MISMATCH",
                )

        with self._lock:
            matrix = np.array(vectors, dtype=np.float32)
            faiss_ids = np.array(
                [self._next_id + i for i in range(len(vectors))], dtype=np.int64
            )

            self._index.add_with_ids(matrix, faiss_ids)
            for i, fid in enumerate(faiss_ids):
                self._id_to_chunk[int(fid)] = chunk_ids[i]
            self._next_id += len(vectors)

            self._save()
        logger.info(f"Added {len(vectors)} vectors to store (total={self.size})")
        return faiss_ids.tolist()

    def search(self, query_vector: list[float], k: int = None, paper_ids: list[str] = None) -> list[dict]:
        """Search for the k most similar vectors, optionally scoped to papers.

        FAISS does not natively filter by metadata, so when ``paper_ids`` is
        provided the search oversamples the FAISS index, resolves the returned
        chunk IDs against MongoDB, keeps only chunks belonging to one of the
        given papers, and truncates to the requested ``k``. If too few chunks
        survive the filter, the oversample is doubled and the search retried,
        up to a configured maximum oversample factor.

        Args:
            query_vector: The query embedding vector.
            k: Number of results to return (default from settings).
            paper_ids: Optional list of paper IDs to scope results to.

        Returns:
            A list of dicts with keys:
                - chunk_id (str): The associated chunk identifier.
                - score (float): Similarity score (cosine distance).
                - position (int): Rank position (0 = most similar).
        """
        k = k or settings.DEFAULT_TOP_K

        if self.size == 0:
            logger.warning("Search attempted on empty index.")
            return []

        matrix = np.array([query_vector], dtype=np.float32)

        if not paper_ids:
            distances, indices = self._index.search(matrix, k)
            return self._format_results(distances[0], indices[0])

        return self._search_paper_scoped(matrix, k, set(paper_ids))

    def _format_results(self, distances, indices) -> list[dict]:
        """Build result dicts from a FAISS distance/index pair."""
        results = []
        for pos, (dist, idx) in enumerate(zip(distances, indices)):
            if idx == -1:
                continue
            chunk_id = self._id_to_chunk.get(int(idx), str(int(idx)))
            results.append({
                "chunk_id": chunk_id,
                "score": float(dist),
                "position": pos,
            })
        return results

    def _search_paper_scoped(self, matrix, k: int, paper_ids: set) -> list[dict]:
        """Oversample, filter by paper ownership, and truncate to k results."""
        oversample_factor = settings.VECTOR_SEARCH_OVERSAMPLE_FACTOR
        max_oversample = k * settings.VECTOR_SEARCH_MAX_OVERSAMPLE_FACTOR
        filtered = []

        while oversample_factor * k <= max_oversample:
            fetch_k = min(oversample_factor * k, self.size)
            distances, indices = self._index.search(matrix, fetch_k)
            results = self._format_results(distances[0], indices[0])
            if not results:
                break

            vector_ids = [r["chunk_id"] for r in results]
            chunks = chunk_model.get_chunks_by_vector_ids(vector_ids)
            chunks_by_id = {c["vector_id"]: c for c in (chunks or [])}

            for r in results:
                chunk = chunks_by_id.get(r["chunk_id"])
                if chunk and str(chunk.get("paper_id")) in paper_ids:
                    filtered.append(r)
                if len(filtered) >= k:
                    break

            if len(filtered) >= k or fetch_k >= self.size:
                break

            oversample_factor *= 2

        return filtered[:k]

    def list_chunk_ids(self) -> set[str]:
        """Return the set of all chunk IDs currently in the store."""
        return set(self._id_to_chunk.values())

    def remove_vectors(self, chunk_ids: list[str]) -> int:
        """Remove vectors associated with given chunk IDs.

        Args:
            chunk_ids: Chunk identifiers to remove.

        Returns:
            Number of vectors removed.
        """
        ids_to_remove = [
            fid for fid, cid in self._id_to_chunk.items()
            if cid in chunk_ids
        ]
        if not ids_to_remove:
            return 0

        with self._lock:
            self._index.remove_ids(np.array(ids_to_remove, dtype=np.int64))
            for fid in ids_to_remove:
                del self._id_to_chunk[fid]
            self._save()
        logger.info(f"Removed {len(ids_to_remove)} vectors from store")
        return len(ids_to_remove)

    @property
    def size(self) -> int:
        """Number of vectors currently in the index."""
        return self._index.ntotal if self._index else 0

    def is_available(self) -> bool:
        """Check whether the store is loaded and functional."""
        return self._index is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _dimension(self) -> int:
        if self._index and self._index.d != 0:
            return self._index.d
        return 0

    def _load_or_create(self):
        os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)

        if os.path.exists(self._index_path):
            try:
                self._index = faiss.read_index(self._index_path)
                if os.path.exists(self._mapping_path):
                    with open(self._mapping_path) as f:
                        raw = json.load(f)
                    self._id_to_chunk = {int(k): v for k, v in raw.items()}
                    self._next_id = max(map(int, raw.keys()), default=-1) + 1
                logger.info(
                    f"Loaded vector store ({self.size} vectors, "
                    f"dim={self._index.d})"
                )
                return
            except Exception:
                logger.exception("Failed to load existing index; creating new one.")

        dim = 384
        self._index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
        self._next_id = 0
        self._id_to_chunk = {}
        logger.info(f"Created new vector store (dim={dim})")

    def _save(self):
        os.makedirs(os.path.dirname(self._index_path), exist_ok=True)
        faiss.write_index(self._index, self._index_path)
        with open(self._mapping_path, "w") as f:
            json.dump(self._id_to_chunk, f)


vector_store = VectorStoreService()
