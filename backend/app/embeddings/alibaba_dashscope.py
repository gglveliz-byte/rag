"""Alibaba DashScope text-embedding-v3 API client with batching and retries."""

import asyncio
import logging
from typing import Any
import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.embeddings.base_embedding import BaseEmbeddingService

logger = logging.getLogger("rag_engine.dashscope")
settings = get_settings()


class AlibabaDashScopeEmbeddings(BaseEmbeddingService):
    """Client for Alibaba DashScope text-embedding-v3 API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        batch_size: int | None = None,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.DASHSCOPE_API_KEY
        self._model = model or settings.DASHSCOPE_MODEL
        self._dimensions = dimensions or settings.EMBEDDING_DIMENSIONS
        # DashScope enforces a maximum batch size of 10 inputs per request
        raw_batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        self._batch_size = min(raw_batch_size, 10)
        self._base_url = (base_url or settings.DASHSCOPE_BASE_URL).rstrip("/")
        # Concurrency semaphore to respect requests per minute
        self._semaphore = asyncio.Semaphore(5)

    def dimensions(self) -> int:
        return self._dimensions

    async def _embed_batch(
        self,
        client: httpx.AsyncClient,
        batch: list[str],
        text_type: str = "document",
    ) -> list[list[float]]:
        """Call DashScope API (OpenAI-compatible) for a batch of up to 25 items."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        # OpenAI-compatible format for embeddings
        payload: dict[str, Any] = {
            "model": self._model,
            "input": batch,
            "dimensions": self._dimensions,
            "encoding_format": "float",
        }

        # Use OpenAI-compatible endpoint path
        # Transform base URL: /api/v1 → /compatible-mode/v1
        compat_base = self._base_url.replace("/api/v1", "/compatible-mode/v1")
        endpoint = f"{compat_base}/embeddings"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                async with self._semaphore:
                    response = await client.post(endpoint, json=payload, headers=headers, timeout=30.0)

                if response.status_code == 200:
                    data = response.json()
                    # OpenAI format: { data: [{ embedding: [...], index: 0 }, ...] }
                    items = data.get("data", [])
                    items.sort(key=lambda x: x.get("index", 0))
                    return [item["embedding"] for item in items]

                if response.status_code == 429:
                    wait_seconds = 2 ** (attempt + 1)
                    logger.warning("DashScope Rate Limit (429). Waiting %ds...", wait_seconds)
                    await asyncio.sleep(wait_seconds)
                    continue

                error_data = response.json() if response.content else {}
                msg = error_data.get("error", {}).get("message", response.text)
                logger.warning("DashScope error from %s (%d): %s", endpoint, response.status_code, msg)

            except httpx.RequestError as exc:
                logger.warning("Network error contacting DashScope (%s): %s", endpoint, exc)

            await asyncio.sleep(1.0 * (attempt + 1))

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error al conectar con el motor de embeddings tras múltiples reintentos.",
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate dense vectors for all texts in chunks of batch_size."""
        if not texts:
            return []

        if not self._api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DASHSCOPE_API_KEY no está configurada. Configure la clave en .env o active USE_MOCK_EMBEDDINGS=true.",
            )

        all_vectors: list[list[float]] = []
        async with httpx.AsyncClient() as client:
            for i in range(0, len(texts), self._batch_size):
                batch = texts[i : i + self._batch_size]
                batch_vectors = await self._embed_batch(client, batch)
                all_vectors.extend(batch_vectors)

        return all_vectors
