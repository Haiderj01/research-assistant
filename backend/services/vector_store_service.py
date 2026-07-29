import json
import os
import threading
import numpy as np
import faiss
from backend.config.settings import settings
from backend.middlewares.error_handler import AppError
from backend.utils.logger import logger


class VectorStoreService:
    """FAISS-based vector store with persistent ID mapping.

    Stores dense embedding vectors and supports similarity search.
    A sidecar mapping file links FAISS internal IDs to external
    chunk/document identifiers (e.g., MongoDB _id strings).
    """

    def __init__(self, index_path: str = None, mapping_path: str = None, vectors_path: str = None):
        self._index_path = index_path or os.path.join(
            settings.VECTOR_STORE_PATH, "index.faiss"
        )
        self._mapping_path = mapping_path or os.path.join(
            settings.VECTOR_STORE_PATH, "id_mapping.json"
        )
        self._vectors_path = vectors_path or os.path.join(
            settings.VECTOR_STORE_PATH, "vectors.npy"
        )
        self._next_id: int = 0
        self._id_to_chunk: dict[int, str] = {}
        self._vectors: dict[int, np.ndarray] = {}
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
                self._vectors[int(fid)] = matrix[i]
            self._next_id += len(vectors)

            self._save()
        logger.info(f"Added {len(vectors)} vectors to store (total={self.size})")
        return faiss_ids.tolist()

    def search(self, query_vector: list[float], k: int = None) -> list[dict]:
        """Search for the k most similar vectors.

        Args:
            query_vector: The query embedding vector.
            k: Number of results to return (default from settings).

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
        distances, indices = self._index.search(matrix, k)

        results = []
        for pos, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:
                continue
            chunk_id = self._id_to_chunk.get(int(idx), str(int(idx)))
            results.append({
                "chunk_id": chunk_id,
                "score": float(dist),
                "position": pos,
            })
        return results

    def remove_vectors(self, chunk_ids: list[str]) -> int:
        """Remove vectors associated with given chunk IDs.

        FAISS does not support efficient deletion in all index types.
        This implementation removes the IDs from the mapping and
        rebuilds the index without the deleted vectors.

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

        for fid in ids_to_remove:
            del self._id_to_chunk[fid]
            self._vectors.pop(fid, None)

        self._rebuild_index()
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
                if os.path.exists(self._vectors_path):
                    arr = np.load(self._vectors_path, allow_pickle=False)
                    self._vectors = {
                        int(fid): arr[i] for i, fid in enumerate(
                            sorted(self._id_to_chunk.keys())
                        )
                    }
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
        self._vectors = {}
        logger.info(f"Created new vector store (dim={dim})")

    def _save(self):
        os.makedirs(os.path.dirname(self._index_path), exist_ok=True)
        faiss.write_index(self._index, self._index_path)
        with open(self._mapping_path, "w") as f:
            json.dump(self._id_to_chunk, f)
        ids = sorted(self._vectors.keys())
        if ids:
            arr = np.array([self._vectors[fid] for fid in ids], dtype=np.float32)
            np.save(self._vectors_path, arr)

    def _rebuild_index(self):
        dim = self._index.d

        if not self._id_to_chunk or not self._vectors:
            self._index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
            self._next_id = 0
            return

        ids = sorted(self._id_to_chunk.keys())
        vectors = [self._vectors[fid] for fid in ids]

        self._index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
        matrix = np.array(vectors, dtype=np.float32)
        faiss_ids = np.array(ids, dtype=np.int64)
        self._index.add_with_ids(matrix, faiss_ids)
        self._next_id = max(ids) + 1 if ids else 0


vector_store = VectorStoreService()
