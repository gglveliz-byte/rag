"""API request and response models for endpoints."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from app.schemas.document import SearchResult


class TargetStore(str, Enum):
    """Supported target vector stores."""

    POSTGRES = "postgres"
    MONGO = "mongo"
    BOTH = "both"


class IngestResponse(BaseModel):
    """Response returned when an ingestion job is created."""

    job_id: str
    status: str
    filename: str
    message: str


class DriveIngestRequest(BaseModel):
    """Request payload to ingest a document from Google Drive."""

    url: str = Field(description="Public Google Drive URL")
    targets: list[str] = Field(default_factory=lambda: ["postgres"])
    tags: list[str] = Field(default_factory=list)
    replace_if_exists: bool = False


class SearchRequest(BaseModel):
    """Search request payload for internal knowledge search."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    store: TargetStore = TargetStore.POSTGRES
    filters: dict[str, Any] | None = None
    tags: list[str] | None = None
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    """Search response payload."""

    query: str
    results: list[SearchResult]
    total_results: int
    query_time_ms: float


class RAGQueryRequest(BaseModel):
    """External LLM consumption query payload."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    tags: list[str] | None = None
    include_formatted_context: bool = True


class RAGChunkItem(BaseModel):
    """Chunk item formatted for external LLM ingestion."""

    chunk_id: str
    content: str
    similarity_score: float
    source_file: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    """High-level response payload for LLMs and AI Agents."""

    query: str
    results_count: int
    context_text: str = Field(description="Pre-formatted text block ready to insert into LLM prompt")
    context_string: str = Field(default="", description="Alias for context_text for client compatibility")
    chunks: list[RAGChunkItem]
    execution_time_ms: float


class JobStatus(str, Enum):
    """Pipeline job lifecycle status."""

    QUEUED = "queued"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    """Status details for an ingestion job."""

    job_id: str
    filename: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    stage_message: str
    created_at: str
    error: str | None = None


class HealthStatus(BaseModel):
    """System health check response."""

    status: str
    postgres_connected: bool
    mongo_connected: bool
    dashscope_configured: bool
    mock_mode: bool
    timestamp: str


class KnowledgeStats(BaseModel):
    """Knowledge base statistics for tenant."""

    total_documents: int
    total_chunks: int
    total_size_bytes: int
    is_ephemeral: bool
    expires_in_hours: float | None = None
