"""Asynchronous client for Alibaba Cloud Qwen LLM using OpenAI-compatible API."""

import logging
from typing import Any
import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

logger = logging.getLogger("rag_engine.llm_client")
settings = get_settings()


class QwenLLMClient:
    """OpenAI-compatible client for Alibaba Cloud Qwen LLM models."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.LLM_API_KEY
        self._base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self._model = model or settings.LLM_MODEL

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """Call Qwen chat completion API with low temperature for strict grounding.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            temperature: Sampling temperature (0.1 for high factual accuracy).
            max_tokens: Maximum tokens in generated completion.

        Returns:
            The textual response content.
        """
        if not self._api_key or not self._api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM_API_KEY no está configurada en el servidor.",
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key.strip()}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(
                    "Qwen API error (%d): %s",
                    response.status_code,
                    response.text[:250],
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error en el servicio de generación LLM ({response.status_code}): {response.text[:150]}",
                )

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="El servicio LLM retornó una respuesta vacía.",
                )

            return choices[0]["message"]["content"].strip()

        except httpx.RequestError as exc:
            logger.error("HTTP request to Qwen API failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Fallo de conexión con el proveedor LLM: {exc}",
            )


qwen_client = QwenLLMClient()
