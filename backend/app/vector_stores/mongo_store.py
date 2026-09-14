"""MongoDB Vector Search store with native and cosine fallback search."""

import logging
from datetime import datetime, timezone
from typing import Any
import motor.motor_asyncio
import numpy as np

from app.core.config import get_settings
from app.schemas.document import Chunk, Document, SearchResult
from app.vector_stores.base_store import VectorStoreBase

logger = logging.getLogger("rag_engine.mongo")
settings = get_settings()


class MongoVectorStore(VectorStoreBase):
    """MongoDB vector store using motor for async operations and hybrid vector search."""

    def __init__(
        self,
        connection_url: str | None = None,
        db_name: str | None = None,
        dimension: int | None = None,
    ) -> None:
        self._url = connection_url or settings.MONGO_URL
        self._db_name = db_name or settings.MONGO_DB_NAME
        self._dim = dimension or settings.EMBEDDING_DIMENSIONS
        self._client: motor.motor_asyncio.AsyncIOMotorClient | None = None

    def _get_db(self):
        if self._client is None:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                self._url,
                serverSelectionTimeoutMS=3000,
            )
        return self._client[self._db_name]

    async def is_connected(self) -> bool:
        try:
            db = self._get_db()
            await db.command("ping")
            return True
        except Exception:
            return False

    async def initialize(self) -> None:
        try:
            db = self._get_db()
            docs_col = db["documents"]
            chunks_col = db["chunks"]

            await docs_col.create_index([("tenant_id", 1)])
            await docs_col.create_index([("tenant_id", 1), ("file_hash", 1)])
            await docs_col.create_index([("is_ephemeral", 1), ("expires_at", 1)])

            await chunks_col.create_index([("tenant_id", 1)])
            await chunks_col.create_index([("tenant_id", 1), ("document_id", 1)])
            logger.info("MongoDB collections and indices initialized successfully.")
        except Exception as exc:
            logger.warning("Could not initialize MongoDB store (may be offline): %s", exc)

    async def insert_chunks(self, doc: Document, chunks: list[Chunk]) -> None:
        db = self._get_db()
        docs_col = db["documents"]
        chunks_col = db["chunks"]

        # Upsert document
        doc_dict = doc.model_dump()
        await docs_col.update_one(
            {"document_id": doc.document_id, "tenant_id": doc.tenant_id},
            {"$set": doc_dict},
            upsert=True,
        )

        # Insert chunks
        if chunks:
            chunk_dicts = [c.model_dump() for c in chunks]
            # Replace existing chunks for this doc to prevent duplicates
            await chunks_col.delete_many({"document_id": doc.document_id, "tenant_id": doc.tenant_id})
            await chunks_col.insert_many(chunk_dicts)

    async def search(
        self,
        tenant_id: str,
        embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        threshold: float = 0.0,
    ) -> list[SearchResult]:
        db = self._get_db()
        chunks_col = db["chunks"]
        docs_col = db["documents"]

        # Strategy 1: Try MongoDB Atlas $vectorSearch aggregation pipeline
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embedding",
                        "queryVector": embedding,
                        "numCandidates": top_k * 10,
                        "limit": top_k,
                        "filter": {"tenant_id": tenant_id},
                    }
                },
                {
                    "$project": {
                        "chunk_id": 1,
                        "document_id": 1,
                        "content": 1,
                        "metadata": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]
            cursor = chunks_col.aggregate(pipeline)
            raw_results = await cursor.to_list(length=top_k)
            if raw_results:
                search_results: list[SearchResult] = []
                for item in raw_results:
                    score = float(item.get("score", 0.0))
                    if score >= threshold:
                        doc = await docs_col.find_one({"document_id": item["document_id"]})
                        filename = doc.get("filename", "") if doc else ""
                        search_results.append(
                            SearchResult(
                                chunk_id=item["chunk_id"],
                                document_id=item["document_id"],
                                content=item["content"],
                                score=score,
                                source_file=filename,
                                metadata=item.get("metadata", {}),
                            )
                        )
                return search_results
        except Exception:
            # Fall back to client-side cosine calculation (for local Docker MongoDB 7)
            pass

        # Strategy 2: Standalone MongoDB cosine similarity ranking
        cursor = chunks_col.find({"tenant_id": tenant_id}, {"chunk_id": 1, "document_id": 1, "content": 1, "embedding": 1, "metadata": 1})
        all_tenant_chunks = await cursor.to_list(length=1000)

        if not all_tenant_chunks:
            return []

        query_vec = np.array(embedding)
        norm_q = np.linalg.norm(query_vec)
        if norm_q == 0:
            return []

        scored_items: list[tuple[float, dict]] = []
        for c in all_tenant_chunks:
            vec = np.array(c.get("embedding", []))
            norm_v = np.linalg.norm(vec)
            if norm_v > 0:
                cos_sim = float(np.dot(query_vec, vec) / (norm_q * norm_v))
                if cos_sim >= threshold:
                    scored_items.append((cos_sim, c))

        # Sort descending by cosine similarity
        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_items = scored_items[:top_k]

        results: list[SearchResult] = []
        for score, item in top_items:
            doc = await docs_col.find_one({"document_id": item["document_id"]})
            filename = doc.get("filename", "") if doc else ""
            results.append(
                SearchResult(
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    content=item["content"],
                    score=score,
                    source_file=filename,
                    metadata=item.get("metadata", {}),
                )
            )
        return results

    async def document_exists(self, tenant_id: str, file_hash: str) -> Document | None:
        db = self._get_db()
        raw = await db["documents"].find_one({"tenant_id": tenant_id, "file_hash": file_hash})
        if not raw:
            return None
        raw.pop("_id", None)
        return Document(**raw)

    async def delete_document(self, tenant_id: str, document_id: str) -> bool:
        db = self._get_db()
        res = await db["documents"].delete_one({"tenant_id": tenant_id, "document_id": document_id})
        await db["chunks"].delete_many({"tenant_id": tenant_id, "document_id": document_id})
        return res.deleted_count > 0

    async def get_all_documents(self, tenant_id: str) -> list[Document]:
        db = self._get_db()
        cursor = db["documents"].find({"tenant_id": tenant_id}).sort("created_at", -1)
        raw_docs = await cursor.to_list(length=1000)
        results = []
        for d in raw_docs:
            d.pop("_id", None)
            results.append(Document(**d))
        return results

    async def get_document_chunks(self, tenant_id: str, document_id: str) -> list[Chunk]:
        db = self._get_db()
        cursor = db["chunks"].find({"tenant_id": tenant_id, "document_id": document_id}).sort("chunk_index", 1)
        raw_chunks = await cursor.to_list(length=5000)
        results = []
        for c in raw_chunks:
            c.pop("_id", None)
            results.append(Chunk(**c))
        return results

    async def get_all_chunks(self, tenant_id: str) -> list[Chunk]:
        db = self._get_db()
        cursor = db["chunks"].find({"tenant_id": tenant_id}).sort("chunk_index", 1)
        raw_chunks = await cursor.to_list(length=50000)
        results = []
        for c in raw_chunks:
            c.pop("_id", None)
            results.append(Chunk(**c))
        return results

    async def get_stats(self, tenant_id: str) -> dict[str, Any]:
        db = self._get_db()
        doc_count = await db["documents"].count_documents({"tenant_id": tenant_id})
        chunk_count = await db["chunks"].count_documents({"tenant_id": tenant_id})

        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {"_id": None, "total_size": {"$sum": "$file_size_bytes"}}},
        ]
        cursor = db["documents"].aggregate(pipeline)
        size_res = await cursor.to_list(length=1)
        total_size = size_res[0]["total_size"] if size_res else 0

        return {
            "total_documents": doc_count,
            "total_chunks": chunk_count,
            "total_size_bytes": total_size,
        }

    async def claim_guest_session(self, guest_session_id: str, user_id: str) -> int:
        guest_tenant = f"guest_{guest_session_id}"
        user_tenant = f"user_{user_id}"
        db = self._get_db()

        res = await db["documents"].update_many(
            {"tenant_id": guest_tenant},
            {"$set": {"tenant_id": user_tenant, "is_ephemeral": False, "expires_at": None}},
        )
        await db["chunks"].update_many(
            {"tenant_id": guest_tenant},
            {"$set": {"tenant_id": user_tenant}},
        )
        return res.modified_count

    async def purge_expired_ephemeral(self) -> int:
        now = datetime.now(timezone.utc)
        db = self._get_db()

        # Find expired document ids
        cursor = db["documents"].find({"is_ephemeral": True, "expires_at": {"$lt": now}}, {"document_id": 1})
        expired_docs = await cursor.to_list(length=1000)
        if not expired_docs:
            return 0

        doc_ids = [d["document_id"] for d in expired_docs]
        del_res = await db["documents"].delete_many({"document_id": {"$in": doc_ids}})
        await db["chunks"].delete_many({"document_id": {"$in": doc_ids}})
        return del_res.deleted_count
