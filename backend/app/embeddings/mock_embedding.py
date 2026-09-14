"""Mock embedding generator for development and testing without API costs."""

import hashlib
import numpy as np

from app.embeddings.base_embedding import BaseEmbeddingService


class MockEmbeddingService(BaseEmbeddingService):
    """Generates deterministic normalized pseudo-embeddings based on text hashes."""

    def __init__(self, dimension: int = 1024) -> None:
        self._dim = dimension

    def dimensions(self) -> int:
        return self._dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            # Seed numpy with SHA-256 integer representation to make it deterministic
            seed_int = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed_int)
            raw_vec = rng.standard_normal(self._dim)
            norm = np.linalg.norm(raw_vec)
            if norm > 0:
                normalized_vec = raw_vec / norm
            else:
                normalized_vec = raw_vec
            results.append(normalized_vec.tolist())
        return results
