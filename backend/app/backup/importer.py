"""Agnostic knowledge base backup importer restoring .ragpkg packages."""

import gzip
import json
from pathlib import Path
from fastapi import HTTPException, status

from app.schemas.document import Chunk, Document
from app.vector_stores.store_manager import store_manager


async def import_tenant_backup(
    file_path: Path,
    tenant_id: str,
    targets: list[str] | None = None,
) -> dict[str, int | str]:
    """Restore documents and vectors from a .ragpkg package into target stores.

    Args:
        file_path: Path to uploaded .ragpkg file.
        tenant_id: Target tenant to import into.
        targets: Target vector stores (defaults to ['postgres']).

    Returns:
        Summary dict of restored counts.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"El archivo de respaldo {file_path} no existe.")

    target_stores = targets or ["postgres"]
    documents_map: dict[str, Document] = {}
    chunks_by_doc: dict[str, list[Chunk]] = {}

    try:
        with gzip.open(file_path, "rt", encoding="utf-8") as gz:
            # 1. First line must be metadata header
            header_line = gz.readline()
            if not header_line:
                raise ValueError("Archivo de respaldo vacío.")
            header = json.loads(header_line)
            if header.get("record_type") != "metadata":
                raise ValueError("Cabecera de paquete .ragpkg inválida o no reconocida.")

            # 2. Process records
            for line in gz:
                line_str = line.strip()
                if not line_str:
                    continue
                record = json.loads(line_str)
                rec_type = record.get("record_type")

                if rec_type == "document":
                    doc_data = record["data"]
                    # Reassign tenant_id to the currently active user/tenant
                    doc_data["tenant_id"] = tenant_id
                    doc = Document(**doc_data)
                    documents_map[doc.document_id] = doc

                elif rec_type == "chunk":
                    chunk_data = record["data"]
                    # Reassign tenant_id
                    chunk_data["tenant_id"] = tenant_id
                    chunk = Chunk(**chunk_data)
                    chunks_by_doc.setdefault(chunk.document_id, []).append(chunk)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al leer y descomprimir el archivo de respaldo .ragpkg: {exc}",
        )

    # 3. Persist into stores
    restored_docs = 0
    restored_chunks = 0

    for doc_id, doc in documents_map.items():
        doc_chunks = chunks_by_doc.get(doc_id, [])
        await store_manager.insert(doc, doc_chunks, target_stores)
        restored_docs += 1
        restored_chunks += len(doc_chunks)

    return {
        "status": "success",
        "restored_documents": restored_docs,
        "restored_chunks": restored_chunks,
        "targets": ", ".join(target_stores),
    }
