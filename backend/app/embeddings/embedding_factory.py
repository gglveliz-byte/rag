"""Embedding service factory and selector."""

from app.core.config import get_settings
from app.embeddings.alibaba_dashscope import AlibabaDashScopeEmbeddings
from app.embeddings.base_embedding import BaseEmbeddingService
from app.embeddings.mock_embedding import MockEmbeddingService

settings = get_settings()


def get_embedding_service() -> BaseEmbeddingService:
    """Return active embedding service based on settings.

    Returns MockEmbeddingService if USE_MOCK_EMBEDDINGS is True or DASHSCOPE_API_KEY is unset,
    otherwise returns AlibabaDashScopeEmbeddings.
    """
    if settings.USE_MOCK_EMBEDDINGS or not settings.DASHSCOPE_API_KEY:
        return MockEmbeddingService(dimension=settings.EMBEDDING_DIMENSIONS)

    return AlibabaDashScopeEmbeddings(
        api_key=settings.DASHSCOPE_API_KEY,
        model=settings.DASHSCOPE_MODEL,
        dimensions=settings.EMBEDDING_DIMENSIONS,
        batch_size=settings.EMBEDDING_BATCH_SIZE,
    )
