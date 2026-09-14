"""Knowledge base exploration, document inspection, stats and deletion routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import TenantContext, get_tenant_context
from app.schemas.api_models import KnowledgeStats
from app.schemas.document import Chunk, Document
from app.vector_stores.store_manager import store_manager

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.get(
    "/documents",
    response_model=list[Document],
    summary="List indexed documents for current tenant",
)
async def list_documents(tenant: TenantContext = Depends(get_tenant_context)) -> list[Document]:
    """Retrieve all indexed documents for the current session/tenant."""
    return await store_manager.get_all_documents(tenant.tenant_id)


@router.get(
    "/documents/{document_id}",
    response_model=dict,
    summary="Get document details and its semantic chunks",
)
async def get_document_details(
    document_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Retrieve document metadata and all generated chunks."""
    docs = await store_manager.get_all_documents(tenant.tenant_id)
    target_doc = next((d for d in docs if d.document_id == document_id), None)

    if not target_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento '{document_id}' no encontrado.",
        )

    chunks = await store_manager.get_document_chunks(tenant.tenant_id, document_id)
    return {
        "document": target_doc,
        "chunks_count": len(chunks),
        "chunks": chunks,
    }


@router.get(
    "/stats",
    response_model=KnowledgeStats,
    summary="Get knowledge base statistics for current tenant",
)
async def get_knowledge_stats(tenant: TenantContext = Depends(get_tenant_context)) -> KnowledgeStats:
    """Get total documents, total chunks and storage footprint."""
    stats = await store_manager.get_stats(tenant.tenant_id)

    expires_in = 24.0 if tenant.is_ephemeral else None

    return KnowledgeStats(
        total_documents=stats.get("total_documents", 0),
        total_chunks=stats.get("total_chunks", 0),
        total_size_bytes=stats.get("total_size_bytes", 0),
        is_ephemeral=tenant.is_ephemeral,
        expires_in_hours=expires_in,
    )


@router.delete(
    "/documents/{document_id}",
    summary="Delete a document and its associated vector chunks",
)
async def delete_document(
    document_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict[str, str]:
    """Delete document and chunks from all vector stores."""
    deleted = await store_manager.delete_document(tenant.tenant_id, document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento '{document_id}' no encontrado o ya eliminado.",
        )
    return {"message": "Documento y chunks eliminados exitosamente."}
