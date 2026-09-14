"""Public retrieval API endpoint designed for external LLMs, AI Agents and LangChain."""

import time
from fastapi import APIRouter, Depends, status

from app.core.auth import TenantContext, get_tenant_context
from app.embeddings.embedding_factory import get_embedding_service
from app.schemas.api_models import RAGChunkItem, RAGQueryRequest, RAGQueryResponse
from app.vector_stores.store_manager import store_manager

router = APIRouter(prefix="/v1/rag", tags=["External LLM & Agent RAG API"])


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Knowledge Base for external LLMs (LangChain, GPTs)",
)
async def query_knowledge_base_for_llm(
    payload: RAGQueryRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> RAGQueryResponse:
    """Retrieve semantically relevant chunks formatted specifically for LLM prompt injection.

    Authenticate using an API Key in the Authorization header:
    `Authorization: Bearer rke_live_...`
    """
    start_time = time.perf_counter()

    # 1. Embed query
    embedder = get_embedding_service()
    query_vectors = await embedder.embed([payload.query])
    query_vector = query_vectors[0]

    # 2. Search isolated tenant memory
    search_results = await store_manager.search(
        tenant_id=tenant.tenant_id,
        embedding=query_vector,
        top_k=payload.top_k,
        threshold=payload.score_threshold,
    )

    # 3. Format chunks and context string
    formatted_context_parts: list[str] = []
    chunk_items: list[RAGChunkItem] = []

    for r in search_results:
        chunk_items.append(
            RAGChunkItem(
                chunk_id=r.chunk_id,
                content=r.content,
                similarity_score=round(r.score, 4),
                source_file=r.source_file,
                metadata=r.metadata,
            )
        )

        # Build clean citation block for LLM prompt
        meta_str = ""
        if "page_number" in r.metadata:
            meta_str = f" (Pág. {r.metadata['page_number']})"
        elif "sheet_name" in r.metadata:
            meta_str = f" (Hoja: {r.metadata['sheet_name']})"

        formatted_context_parts.append(
            f"[Fuente: {r.source_file}{meta_str} | Similitud: {r.score:.2f}]:\n{r.content}"
        )

    context_text = "\n\n---\n\n".join(formatted_context_parts)
    execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return RAGQueryResponse(
        query=payload.query,
        results_count=len(chunk_items),
        context_text=context_text,
        chunks=chunk_items,
        execution_time_ms=execution_time_ms,
    )
