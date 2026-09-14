"""Multi-store coordinator and router for PostgreSQL and MongoDB."""

import logging
from typing import Any
from fastapi import HTTPException, status

from app.schemas.api_models import TargetStore
from app.schemas.document import Chunk, Document, SearchResult
from app.vector_stores.mongo_store import MongoVectorStore
from app.vector_stores.postgres_store import PostgresVectorStore

logger = logging.getLogger("rag_engine.store_manager")


class StoreManager:
    """Coordinates persistence and search across PostgreSQL and MongoDB."""

    def __init__(self) -> None:
        self.postgres = PostgresVectorStore()
        self.mongo = MongoVectorStore()

    async def initialize(self) -> None:
        """Initialize both stores asynchronously."""
        await self.postgres.initialize()
        await self.mongo.initialize()

    async def get_health(self) -> tuple[bool, bool]:
        """Check connection status for (postgres, mongo)."""
        pg_ok = await self.postgres.is_connected()
        mg_ok = await self.mongo.is_connected()
        return pg_ok, mg_ok

    async def insert(self, doc: Document, chunks: list[Chunk], targets: list[str]) -> list[str]:
        """Insert document and chunks into requested target stores.

        Args:
            doc: Document metadata object.
            chunks: Chunks with embeddings.
            targets: List containing 'postgres', 'mongo', or 'both'.

        Returns:
            List of stores where insertion succeeded.
        """
        successful_targets: list[str] = []

        if "postgres" in targets or "both" in targets:
            try:
                await self.postgres.insert_chunks(doc, chunks)
                successful_targets.append("postgres")
            except Exception as exc:
                logger.error("Failed to insert into PostgreSQL: %s", exc)

        if "mongo" in targets or "both" in targets:
            try:
                await self.mongo.insert_chunks(doc, chunks)
                successful_targets.append("mongo")
            except Exception as exc:
                logger.error("Failed to insert into MongoDB: %s", exc)

        if not successful_targets:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo persistir el documento en ninguna base de datos vectorial de destino.",
            )

        return successful_targets

    async def search(
        self,
        tenant_id: str,
        embedding: list[float],
        top_k: int = 5,
        store: TargetStore = TargetStore.POSTGRES,
        filters: dict[str, Any] | None = None,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        """Search vector database by similarity, with automatic fallback if primary is unreachable."""
        if store == TargetStore.POSTGRES:
            try:
                return await self.postgres.search(tenant_id, embedding, top_k, filters, threshold)
            except Exception as exc:
                logger.warning("Postgres search failed (%s), attempting Mongo fallback...", exc)
                try:
                    return await self.mongo.search(tenant_id, embedding, top_k, filters, threshold)
                except Exception as m_exc:
                    logger.warning("Both vector stores unreachable (%s). Returning empty list.", m_exc)
                    return []

        if store == TargetStore.MONGO:
            try:
                return await self.mongo.search(tenant_id, embedding, top_k, filters, threshold)
            except Exception as exc:
                logger.warning("Mongo search failed (%s), attempting Postgres fallback...", exc)
                try:
                    return await self.postgres.search(tenant_id, embedding, top_k, filters, threshold)
                except Exception as p_exc:
                    logger.warning("Both vector stores unreachable (%s). Returning empty list.", p_exc)
                    return []

        # Both: perform on both, merge results by highest score, deduplicate by chunk_id
        pg_res = []
        mg_res = []
        try:
            pg_res = await self.postgres.search(tenant_id, embedding, top_k, filters, threshold)
        except Exception:
            pass
        try:
            mg_res = await self.mongo.search(tenant_id, embedding, top_k, filters, threshold)
        except Exception:
            pass

        merged_dict: dict[str, SearchResult] = {}
        for r in pg_res + mg_res:
            if r.chunk_id not in merged_dict or r.score > merged_dict[r.chunk_id].score:
                merged_dict[r.chunk_id] = r

        merged_list = sorted(merged_dict.values(), key=lambda x: x.score, reverse=True)
        return merged_list[:top_k]

    async def document_exists(self, tenant_id: str, file_hash: str) -> Document | None:
        """Check if file hash exists in either store."""
        try:
            doc = await self.postgres.document_exists(tenant_id, file_hash)
            if doc:
                return doc
        except Exception:
            pass

        try:
            doc = await self.mongo.document_exists(tenant_id, file_hash)
            if doc:
                return doc
        except Exception:
            pass

        return None

    async def delete_document(self, tenant_id: str, document_id: str) -> bool:
        """Delete from all active stores."""
        pg_del = False
        mg_del = False
        try:
            pg_del = await self.postgres.delete_document(tenant_id, document_id)
        except Exception:
            pass
        try:
            mg_del = await self.mongo.delete_document(tenant_id, document_id)
        except Exception:
            pass
        return pg_del or mg_del

    async def get_all_documents(self, tenant_id: str) -> list[Document]:
        """Fetch documents from PostgreSQL or fallback to MongoDB. Returns [] if offline."""
        try:
            return await self.postgres.get_all_documents(tenant_id)
        except Exception:
            pass
        try:
            return await self.mongo.get_all_documents(tenant_id)
        except Exception:
            return []

    async def get_document_chunks(self, tenant_id: str, document_id: str) -> list[Chunk]:
        """Fetch chunks for specific document. Returns [] if offline."""
        try:
            return await self.postgres.get_document_chunks(tenant_id, document_id)
        except Exception:
            pass
        try:
            return await self.mongo.get_document_chunks(tenant_id, document_id)
        except Exception:
            return []

    async def get_all_chunks(self, tenant_id: str) -> list[Chunk]:
        """Export all chunks for tenant. Returns [] if offline."""
        try:
            return await self.postgres.get_all_chunks(tenant_id)
        except Exception:
            pass
        try:
            return await self.mongo.get_all_chunks(tenant_id)
        except Exception:
            return []

    async def get_stats(self, tenant_id: str) -> dict[str, Any]:
        """Get stats for tenant. Returns default zero-stats if offline."""
        try:
            return await self.postgres.get_stats(tenant_id)
        except Exception:
            pass
        try:
            return await self.mongo.get_stats(tenant_id)
        except Exception:
            return {
                "tenant_id": tenant_id,
                "total_documents": 0,
                "total_chunks": 0,
                "storage": "offline",
            }

    async def claim_guest_session(self, guest_session_id: str, user_id: str) -> int:
        """Claim session on both PostgreSQL and MongoDB."""
        claimed = 0
        try:
            claimed += await self.postgres.claim_guest_session(guest_session_id, user_id)
        except Exception:
            pass
        try:
            claimed += await self.mongo.claim_guest_session(guest_session_id, user_id)
        except Exception:
            pass
        return claimed

    async def purge_expired(self) -> int:
        """Purge expired ephemeral documents on both stores."""
        purged = 0
        try:
            purged += await self.postgres.purge_expired_ephemeral()
        except Exception:
            pass
        try:
            purged += await self.mongo.purge_expired_ephemeral()
        except Exception:
            pass
        return purged


# Global StoreManager singleton
store_manager = StoreManager()
