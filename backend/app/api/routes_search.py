"""Semantic vector similarity search route."""

import time
from fastapi import APIRouter, Depends, status

from app.core.auth import TenantContext, get_tenant_context
from app.embeddings.embedding_factory import get_embedding_service
from app.schemas.api_models import SearchRequest, SearchResponse
from app.vector_stores.store_manager import store_manager

router = APIRouter(prefix="/search", tags=["Vector Search"])


@router.post(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic vector search across indexed knowledge base",
)
async def search_vectors(
    payload: SearchRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> SearchResponse:
    """Execute vector similarity search across documents in PostgreSQL, MongoDB or both."""
    start_time = time.perf_counter()

    # 1. Generate query embedding
    embedder = get_embedding_service()
    query_embeddings = await embedder.embed([payload.query])
    query_vec = query_embeddings[0]

    # 2. Query target vector store
    results = await store_manager.search(
        tenant_id=tenant.tenant_id,
        embedding=query_vec,
        top_k=payload.top_k,
        store=payload.store,
        filters=payload.filters,
        threshold=payload.score_threshold,
    )

    query_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return SearchResponse(
        query=payload.query,
        results=results,
        total_results=len(results),
        query_time_ms=query_time_ms,
    )
