"""Agnostic knowledge base backup exporter creating portable .ragpkg packages."""

import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.vector_stores.store_manager import store_manager

settings = get_settings()


async def export_tenant_backup(tenant_id: str) -> Path:
    """Serialize all documents and vector chunks for a tenant into a .ragpkg file.

    Args:
        tenant_id: Tenant identifier.

    Returns:
        Path to the generated .ragpkg file.
    """
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    docs = await store_manager.get_all_documents(tenant_id)
    chunks = await store_manager.get_all_chunks(tenant_id)

    if not docs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay documentos en esta base de conocimiento para exportar.",
        )

    now = datetime.now(timezone.utc)
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    clean_tenant = tenant_id.replace(":", "_").replace("/", "_")
    output_filename = f"knowledge_backup_{clean_tenant}_{timestamp_str}.ragpkg"
    output_path = settings.BACKUP_DIR / output_filename

    # Header metadata
    header_record = {
        "record_type": "metadata",
        "format_version": "1.0.0",
        "created_at": now.isoformat(),
        "tenant_id": tenant_id,
        "total_documents": len(docs),
        "total_chunks": len(chunks),
    }

    with gzip.open(output_path, "wt", encoding="utf-8") as gz:
        # 1. Header
        gz.write(json.dumps(header_record) + "\n")

        # 2. Documents
        for doc in docs:
            doc_record = {
                "record_type": "document",
                "data": doc.model_dump(mode="json"),
            }
            gz.write(json.dumps(doc_record) + "\n")

        # 3. Chunks
        for chunk in chunks:
            chunk_record = {
                "record_type": "chunk",
                "data": chunk.model_dump(mode="json"),
            }
            gz.write(json.dumps(chunk_record) + "\n")

    return output_path
