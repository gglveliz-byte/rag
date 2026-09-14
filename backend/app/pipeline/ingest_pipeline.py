"""Primary asynchronous ingestion worker: dedup, extract, chunk, embed and store."""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.chunking.semantic_chunker import SemanticChunker
from app.core.config import get_settings
from app.core.security import compute_file_sha256
from app.embeddings.embedding_factory import get_embedding_service
from app.loaders.loader_factory import loader_factory
from app.pipeline.job_manager import job_manager
from app.schemas.api_models import JobStatus
from app.schemas.document import Document
from app.vector_stores.store_manager import store_manager

logger = logging.getLogger("rag_engine.pipeline")
settings = get_settings()


async def run_ingestion_pipeline(
    job_id: str,
    file_path: Path,
    original_filename: str,
    tenant_id: str,
    is_ephemeral: bool,
    targets: list[str],
    tags: list[str] | None = None,
    replace_if_exists: bool = False,
) -> None:
    """Execute asynchronous end-to-end ingestion pipeline for a document."""
    try:
        # 1. Deduplication check
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.EXTRACTING,
            progress=10,
            stage_message="Calculando hash SHA-256 y verificando duplicados...",
        )
        file_hash = compute_file_sha256(file_path)
        existing_doc = await store_manager.document_exists(tenant_id, file_hash)

        if existing_doc and not replace_if_exists:
            err_msg = f"El archivo '{original_filename}' ya existe en la base de conocimiento (Doc ID: {existing_doc.document_id})."
            await job_manager.update_progress(
                job_id=job_id,
                status=JobStatus.FAILED,
                progress=10,
                stage_message=err_msg,
                error=err_msg,
            )
            return

        if existing_doc and replace_if_exists:
            logger.info("Replacing existing document %s...", existing_doc.document_id)
            await store_manager.delete_document(tenant_id, existing_doc.document_id)

        # 2. Text extraction
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.EXTRACTING,
            progress=25,
            stage_message=f"Extrayendo texto y metadatos con loader especializado...",
        )
        extracted = loader_factory.extract(file_path)

        # 3. Semantic Chunking
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.CHUNKING,
            progress=50,
            stage_message="Analizando cohesión semántica y detectando rupturas temáticas...",
        )
        document_id = str(job_id)
        chunker = SemanticChunker()
        chunks = await chunker.chunk(
            text=extracted.content,
            document_id=document_id,
            tenant_id=tenant_id,
            metadata=extracted.metadata,
        )

        if not chunks:
            raise ValueError("No se pudieron generar chunks del documento extraído.")

        # 4. Dense Vectorization (Embeddings)
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.EMBEDDING,
            progress=75,
            stage_message=f"Generando vectores densos (1024 dims) para {len(chunks)} fragmentos...",
        )
        embedder = get_embedding_service()
        chunk_texts = [c.content for c in chunks]
        embeddings = await embedder.embed(chunk_texts)

        for i, emb in enumerate(embeddings):
            chunks[i].embedding = emb

        # 5. Persistence
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.STORING,
            progress=90,
            stage_message=f"Persistiendo vectores en bases de datos ({', '.join(targets)})...",
        )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=settings.GUEST_SESSION_TTL_HOURS) if is_ephemeral else None

        doc = Document(
            document_id=document_id,
            tenant_id=tenant_id,
            filename=original_filename,
            file_hash=file_hash,
            file_type=extracted.file_type,
            file_size_bytes=extracted.file_size_bytes,
            total_chunks=len(chunks),
            tags=tags or [],
            custom_metadata=extracted.metadata,
            created_at=now,
            is_ephemeral=is_ephemeral,
            expires_at=expires_at,
            version=1,
        )

        persisted_targets = await store_manager.insert(doc, chunks, targets)

        # 6. Completed
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            stage_message=f"Indexación exitosa: {len(chunks)} chunks guardados en {', '.join(persisted_targets)}.",
            extra_data={
                "document_id": document_id,
                "total_chunks": len(chunks),
                "targets": persisted_targets,
                "is_ephemeral": is_ephemeral,
            },
        )
        logger.info("Ingestion job %s completed successfully for document %s", job_id, original_filename)

    except Exception as exc:
        logger.error("Ingestion pipeline failed for job %s: %s", job_id, exc, exc_info=True)
        await job_manager.update_progress(
            job_id=job_id,
            status=JobStatus.FAILED,
            progress=0,
            stage_message=f"Error en el pipeline: {exc}",
            error=str(exc),
        )
