"""Abstract base class for all vector persistence stores."""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas.document import Chunk, Document, SearchResult


class VectorStoreBase(ABC):
    """Abstract interface for database vector stores with multi-tenancy."""

    @abstractmethod
    async def initialize(self) -> None:
        """Create tables, collections, extensions and vector indices."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Verify database connectivity."""
        pass

    @abstractmethod
    async def insert_chunks(self, doc: Document, chunks: list[Chunk]) -> None:
        """Persist document metadata and its vector chunks."""
        pass

    @abstractmethod
    async def search(
        self,
        tenant_id: str,
        embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        """Search for semantically similar chunks belonging to tenant."""
        pass

    @abstractmethod
    async def document_exists(self, tenant_id: str, file_hash: str) -> Document | None:
        """Check if file with SHA-256 hash already exists for tenant."""
        pass

    @abstractmethod
    async def delete_document(self, tenant_id: str, document_id: str) -> bool:
        """Delete document and all associated chunks for tenant."""
        pass

    @abstractmethod
    async def get_all_documents(self, tenant_id: str) -> list[Document]:
        """List all documents for tenant."""
        pass

    @abstractmethod
    async def get_document_chunks(self, tenant_id: str, document_id: str) -> list[Chunk]:
        """Get all chunks for a specific document."""
        pass

    @abstractmethod
    async def get_all_chunks(self, tenant_id: str) -> list[Chunk]:
        """Export all chunks for tenant (used in backup exporter)."""
        pass

    @abstractmethod
    async def get_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get counts of documents and chunks for tenant."""
        pass

    @abstractmethod
    async def claim_guest_session(self, guest_session_id: str, user_id: str) -> int:
        """Transfer documents from guest session to authenticated user, removing 24h TTL."""
        pass

    @abstractmethod
    async def purge_expired_ephemeral(self) -> int:
        """Delete all documents and chunks where is_ephemeral=True and expires_at < NOW()."""
        pass
