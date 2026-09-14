"""PostgreSQL + pgvector vector store implementation with HNSW indexing and multi-tenancy."""

import json
import logging
from datetime import datetime, timezone
from typing import Any
import psycopg
from pgvector.psycopg import register_vector_async

from app.core.config import get_settings
from app.schemas.document import Chunk, Document, SearchResult
from app.vector_stores.base_store import VectorStoreBase

logger = logging.getLogger("rag_engine.postgres")
settings = get_settings()


class PostgresVectorStore(VectorStoreBase):
    """PostgreSQL pgvector store using async psycopg3 and HNSW cosine distance."""

    def __init__(self, connection_url: str | None = None, dimension: int | None = None) -> None:
        self._url = connection_url or settings.POSTGRES_URL
        self._dim = dimension or settings.EMBEDDING_DIMENSIONS
        self._initialized = False

    async def _get_connection(self) -> psycopg.AsyncConnection:
        """Establish async connection and register vector type."""
        conn = await psycopg.AsyncConnection.connect(self._url, connect_timeout=10)
        await register_vector_async(conn)
        return conn

    async def is_connected(self) -> bool:
        """Check if PostgreSQL is accessible."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1;")
                    return True
        except Exception as exc:
            logger.warning("Postgres is_connected failed: %s", exc)
            return False

    async def initialize(self) -> None:
        """Create vector extension, tables and HNSW index."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    # 1. Enable extension
                    await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                    # 2. Documents table
                    await cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS documents (
                            document_id VARCHAR(64) PRIMARY KEY,
                            tenant_id VARCHAR(64) NOT NULL,
                            filename TEXT NOT NULL,
                            file_hash VARCHAR(64) NOT NULL,
                            file_type VARCHAR(16) NOT NULL,
                            file_size_bytes BIGINT NOT NULL,
                            total_chunks INT NOT NULL DEFAULT 0,
                            tags JSONB DEFAULT '[]'::jsonb,
                            project VARCHAR(128),
                            custom_metadata JSONB DEFAULT '{}'::jsonb,
                            created_at TIMESTAMPTZ NOT NULL,
                            is_ephemeral BOOLEAN NOT NULL DEFAULT TRUE,
                            expires_at TIMESTAMPTZ,
                            version INT NOT NULL DEFAULT 1
                        );
                        CREATE INDEX IF NOT EXISTS idx_docs_tenant ON documents(tenant_id);
                        CREATE INDEX IF NOT EXISTS idx_docs_hash ON documents(tenant_id, file_hash);
                        CREATE INDEX IF NOT EXISTS idx_docs_ephemeral ON documents(is_ephemeral, expires_at);
                        """
                    )

                    # 3. Chunks table
                    await cur.execute(
                        f"""
                        CREATE TABLE IF NOT EXISTS chunks (
                            chunk_id VARCHAR(64) PRIMARY KEY,
                            document_id VARCHAR(64) NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
                            tenant_id VARCHAR(64) NOT NULL,
                            content TEXT NOT NULL,
                            embedding vector({self._dim}) NOT NULL,
                            chunk_index INT NOT NULL,
                            token_count INT NOT NULL DEFAULT 0,
                            metadata JSONB DEFAULT '{{}}'::jsonb
                        );
                        CREATE INDEX IF NOT EXISTS idx_chunks_tenant ON chunks(tenant_id);
                        CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id);
                        CREATE INDEX IF NOT EXISTS idx_chunks_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
                        """
                    )
                await conn.commit()
                self._initialized = True
                logger.info("PostgreSQL pgvector tables and HNSW indices initialized successfully.")
        except Exception as exc:
            logger.warning("Could not initialize PostgreSQL store (may be offline): %s", exc)

    async def insert_chunks(self, doc: Document, chunks: list[Chunk]) -> None:
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                # Upsert Document
                await cur.execute(
                    """
                    INSERT INTO documents (
                        document_id, tenant_id, filename, file_hash, file_type,
                        file_size_bytes, total_chunks, tags, project,
                        custom_metadata, created_at, is_ephemeral, expires_at, version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (document_id) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        total_chunks = EXCLUDED.total_chunks,
                        tags = EXCLUDED.tags,
                        custom_metadata = EXCLUDED.custom_metadata,
                        is_ephemeral = EXCLUDED.is_ephemeral,
                        expires_at = EXCLUDED.expires_at;
                    """,
                    (
                        doc.document_id,
                        doc.tenant_id,
                        doc.filename,
                        doc.file_hash,
                        doc.file_type,
                        doc.file_size_bytes,
                        doc.total_chunks,
                        json.dumps(doc.tags),
                        doc.project,
                        json.dumps(doc.custom_metadata),
                        doc.created_at,
                        doc.is_ephemeral,
                        doc.expires_at,
                        doc.version,
                    ),
                )

                # Batch insert chunks
                for chunk in chunks:
                    await cur.execute(
                        """
                        INSERT INTO chunks (
                            chunk_id, document_id, tenant_id, content,
                            embedding, chunk_index, token_count, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO NOTHING;
                        """,
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.tenant_id,
                            chunk.content,
                            chunk.embedding,
                            chunk.chunk_index,
                            chunk.token_count,
                            json.dumps(chunk.metadata),
                        ),
                    )
            await conn.commit()

    async def search(
        self,
        tenant_id: str,
        embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                # 1 - (embedding <=> query) equals cosine similarity
                query = """
                    SELECT
                        c.chunk_id,
                        c.document_id,
                        c.content,
                        (1 - (c.embedding <=> %s::vector)) as score,
                        d.filename as source_file,
                        c.metadata
                    FROM chunks c
                    JOIN documents d ON d.document_id = c.document_id
                    WHERE c.tenant_id = %s
                      AND (1 - (c.embedding <=> %s::vector)) >= %s
                    ORDER BY score DESC
                    LIMIT %s;
                """
                await cur.execute(query, (embedding, tenant_id, embedding, threshold, top_k))
                rows = await cur.fetchall()

                results: list[SearchResult] = []
                for row in rows:
                    chunk_id, doc_id, content, score, source_file, meta = row
                    meta_dict = meta if isinstance(meta, dict) else json.loads(meta or "{}")
                    results.append(
                        SearchResult(
                            chunk_id=chunk_id,
                            document_id=doc_id,
                            content=content,
                            score=float(score),
                            source_file=source_file,
                            metadata=meta_dict,
                        )
                    )
                return results

    async def document_exists(self, tenant_id: str, file_hash: str) -> Document | None:
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT document_id, tenant_id, filename, file_hash, file_type,
                           file_size_bytes, total_chunks, tags, project, custom_metadata,
                           created_at, is_ephemeral, expires_at, version
                    FROM documents
                    WHERE tenant_id = %s AND file_hash = %s
                    LIMIT 1;
                    """,
                    (tenant_id, file_hash),
                )
                row = await cur.fetchone()
                if not row:
                    return None
                return self._row_to_document(row)

    async def delete_document(self, tenant_id: str, document_id: str) -> bool:
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM documents WHERE tenant_id = %s AND document_id = %s;",
                    (tenant_id, document_id),
                )
                deleted = cur.rowcount > 0
            await conn.commit()
            return deleted

    async def get_all_documents(self, tenant_id: str) -> list[Document]:
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT document_id, tenant_id, filename, file_hash, file_type,
                           file_size_bytes, total_chunks, tags, project, custom_metadata,
                           created_at, is_ephemeral, expires_at, version
                    FROM documents
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC;
                    """,
                    (tenant_id,),
                )
                rows = await cur.fetchall()
                return [self._row_to_document(r) for r in rows]

    async def get_document_chunks(self, tenant_id: str, document_id: str) -> list[Chunk]:
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT chunk_id, document_id, tenant_id, content, embedding, chunk_index, token_count, metadata
                    FROM chunks
                    WHERE tenant_id = %s AND document_id = %s
                    ORDER BY chunk_index ASC;
                    """,
                    (tenant_id, document_id),
                )
                rows = await cur.fetchall()
                return [self._row_to_chunk(r) for r in rows]

    async def get_all_chunks(self, tenant_id: str) -> list[Chunk]:
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT chunk_id, document_id, tenant_id, content, embedding, chunk_index, token_count, metadata
                    FROM chunks
                    WHERE tenant_id = %s
                    ORDER BY document_id, chunk_index ASC;
                    """,
                    (tenant_id,),
                )
                rows = await cur.fetchall()
                return [self._row_to_chunk(r) for r in rows]

    async def get_stats(self, tenant_id: str) -> dict[str, Any]:
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT
                        COUNT(DISTINCT d.document_id),
                        COUNT(c.chunk_id),
                        COALESCE(SUM(d.file_size_bytes), 0)
                    FROM documents d
                    LEFT JOIN chunks c ON c.document_id = d.document_id
                    WHERE d.tenant_id = %s;
                    """,
                    (tenant_id,),
                )
                doc_count, chunk_count, size_bytes = await cur.fetchone()
                return {
                    "total_documents": doc_count or 0,
                    "total_chunks": chunk_count or 0,
                    "total_size_bytes": size_bytes or 0,
                }

    async def claim_guest_session(self, guest_session_id: str, user_id: str) -> int:
        guest_tenant = f"guest_{guest_session_id}"
        user_tenant = f"user_{user_id}"

        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                # Update documents
                await cur.execute(
                    """
                    UPDATE documents
                    SET tenant_id = %s, is_ephemeral = FALSE, expires_at = NULL
                    WHERE tenant_id = %s;
                    """,
                    (user_tenant, guest_tenant),
                )
                claimed_docs = cur.rowcount

                # Update chunks
                await cur.execute(
                    """
                    UPDATE chunks
                    SET tenant_id = %s
                    WHERE tenant_id = %s;
                    """,
                    (user_tenant, guest_tenant),
                )
            await conn.commit()
            return claimed_docs

    async def purge_expired_ephemeral(self) -> int:
        now = datetime.now(timezone.utc)
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM documents
                    WHERE is_ephemeral = TRUE AND expires_at < %s;
                    """,
                    (now,),
                )
                purged = cur.rowcount
            await conn.commit()
            return purged

    def _row_to_document(self, row: tuple) -> Document:
        tags = row[7] if isinstance(row[7], list) else json.loads(row[7] or "[]")
        meta = row[9] if isinstance(row[9], dict) else json.loads(row[9] or "{}")
        return Document(
            document_id=row[0],
            tenant_id=row[1],
            filename=row[2],
            file_hash=row[3],
            file_type=row[4],
            file_size_bytes=int(row[5]),
            total_chunks=int(row[6]),
            tags=tags,
            project=row[8],
            custom_metadata=meta,
            created_at=row[10],
            is_ephemeral=bool(row[11]),
            expires_at=row[12],
            version=int(row[13]),
        )

    def _row_to_chunk(self, row: tuple) -> Chunk:
        meta = row[7] if isinstance(row[7], dict) else json.loads(row[7] or "{}")
        # Embedding may come as pgvector Vector object, list, numpy array or None
        emb = row[4]
        if hasattr(emb, "to_list"):
            emb_list = emb.to_list()
        elif hasattr(emb, "tolist"):
            emb_list = emb.tolist()
        elif hasattr(emb, "to_numpy"):
            emb_list = emb.to_numpy().tolist()
        elif isinstance(emb, (list, tuple)):
            emb_list = list(emb)
        elif emb is None:
            emb_list = []
        else:
            try:
                emb_list = list(emb)
            except Exception:
                emb_list = []

        return Chunk(
            chunk_id=row[0],
            document_id=row[1],
            tenant_id=row[2],
            content=row[3],
            embedding=emb_list,
            chunk_index=int(row[5]),
            token_count=int(row[6]),
            metadata=meta,
        )

