"""Abstract base class for document chunkers."""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.document import Chunk


class BaseChunker(ABC):
    """Abstract interface for text partitioning and chunking strategies."""

    @abstractmethod
    async def chunk(
        self,
        text: str,
        document_id: str,
        tenant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """Split document text into cohesive chunks.

        Args:
            text: Extracted full text of the document.
            document_id: Parent document identifier.
            tenant_id: Tenant identifier for multi-tenancy.
            metadata: Base metadata to inherit into chunks.

        Returns:
            List of Chunk objects.
        """
        pass
