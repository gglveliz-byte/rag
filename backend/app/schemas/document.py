"""Document, Chunk and SearchResult Pydantic models."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ExtractedDocument(BaseModel):
    """Raw text and metadata extracted from a file by a loader."""

    filename: str
    file_type: str
    file_size_bytes: int
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Indexed document metadata in the RAG knowledge engine."""

    document_id: str = Field(description="Unique UUID string")
    tenant_id: str = Field(description="Tenant identifier for multi-tenancy isolation")
    filename: str
    file_hash: str = Field(description="SHA-256 hex digest of file contents for deduplication")
    file_type: str
    file_size_bytes: int
    total_chunks: int = 0
    tags: list[str] = Field(default_factory=list)
    project: str | None = None
    custom_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    is_ephemeral: bool = True
    expires_at: datetime | None = None
    version: int = 1


class Chunk(BaseModel):
    """Single semantic chunk with vector embedding and metadata."""

    chunk_id: str = Field(description="Unique UUID string")
    document_id: str = Field(description="Parent document UUID")
    tenant_id: str = Field(description="Tenant identifier for multi-tenancy isolation")
    content: str
    embedding: list[float] = Field(default_factory=list)
    chunk_index: int
    token_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Result item returned by vector similarity search."""

    chunk_id: str
    document_id: str
    content: str
    score: float = Field(description="Cosine similarity score (0.0 to 1.0)")
    source_file: str
    metadata: dict[str, Any] = Field(default_factory=dict)
