"""Abstract base class for vector embedding services."""

from abc import ABC, abstractmethod


class BaseEmbeddingService(ABC):
    """Abstract interface for text embedding models."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate dense vector embeddings for a list of texts.

        Args:
            texts: List of strings to vectorize.

        Returns:
            List of float vectors, each of size self.dimensions().
        """
        pass

    @abstractmethod
    def dimensions(self) -> int:
        """Return the vector dimensionality (e.g. 1024)."""
        pass
