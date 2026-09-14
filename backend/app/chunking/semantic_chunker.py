"""Semantic chunker based on sentence embedding cosine similarity transitions."""

import re
import uuid
from typing import Any
import numpy as np

from app.chunking.base_chunker import BaseChunker
from app.embeddings.base_embedding import BaseEmbeddingService
from app.embeddings.embedding_factory import get_embedding_service
from app.schemas.document import Chunk


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving paragraphs, list items and table rows."""
    paragraphs = text.split("\n\n")
    sentences: list[str] = []

    for para in paragraphs:
        cleaned_para = para.strip()
        if not cleaned_para:
            continue

        # If it's a table row or structured header, keep it as single proposition
        if cleaned_para.startswith("[Fila") or cleaned_para.startswith("[Tabla") or cleaned_para.startswith("==="):
            for line in cleaned_para.split("\n"):
                line_str = line.strip()
                if line_str:
                    sentences.append(line_str)
            continue

        # Sentence split regex on punctuation followed by space or newline
        raw_sentences = re.split(r"(?<=[.?!;])\s+(?=[A-ZÁÉÍÓÚÑa-z0-9])", cleaned_para)
        for s in raw_sentences:
            s_clean = s.strip()
            if s_clean:
                sentences.append(s_clean)

    return sentences


def estimate_token_count(text: str) -> int:
    """Approximate token count (roughly 1.3 tokens per word for multilingual text)."""
    words = len(text.split())
    return max(1, int(words * 1.3))


class SemanticChunker(BaseChunker):
    """Chunks text semantically by detecting significant thematic divergence between sentences."""

    def __init__(
        self,
        embedding_service: BaseEmbeddingService | None = None,
        min_tokens: int = 50,
        max_tokens: int = 500,
        similarity_threshold_percentile: float = 85.0,
    ) -> None:
        self._embedder = embedding_service or get_embedding_service()
        self._min_tokens = min_tokens
        self._max_tokens = max_tokens
        self._percentile = similarity_threshold_percentile

    async def chunk(
        self,
        text: str,
        document_id: str,
        tenant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        base_meta = metadata or {}
        sentences = split_into_sentences(text)

        if not sentences:
            return []

        # If text is too short, return as a single chunk
        if len(sentences) <= 2:
            single_text = " ".join(sentences)
            return [
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    tenant_id=tenant_id,
                    content=single_text,
                    embedding=[],  # Will be populated during embedding phase
                    chunk_index=0,
                    token_count=estimate_token_count(single_text),
                    metadata={**base_meta, "chunk_strategy": "single_short_doc"},
                )
            ]

        # Generate embeddings for individual sentences to detect thematic boundaries
        sentence_embeddings = await self._embedder.embed(sentences)

        # Compute cosine distances between adjacent sentences
        distances: list[float] = []
        for i in range(len(sentence_embeddings) - 1):
            v1 = np.array(sentence_embeddings[i])
            v2 = np.array(sentence_embeddings[i + 1])
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 > 0 and norm2 > 0:
                sim = float(np.dot(v1, v2) / (norm1 * norm2))
                dist = 1.0 - sim
            else:
                dist = 0.5
            distances.append(dist)

        # Determine breakpoint threshold
        if distances:
            breakpoint_distance = float(np.percentile(distances, self._percentile))
        else:
            breakpoint_distance = 0.3

        # Form chunks by aggregating sentences until breakpoint or size limits
        chunks: list[Chunk] = []
        current_sentences: list[str] = [sentences[0]]
        current_tokens: int = estimate_token_count(sentences[0])

        for i in range(len(distances)):
            dist = distances[i]
            next_sentence = sentences[i + 1]
            next_tokens = estimate_token_count(next_sentence)

            # Check if this transition represents a semantic break
            is_semantic_break = dist >= breakpoint_distance
            exceeds_max = (current_tokens + next_tokens) > self._max_tokens
            meets_min = current_tokens >= self._min_tokens

            if (is_semantic_break and meets_min) or exceeds_max:
                # Seal current chunk
                chunk_text = " ".join(current_sentences).strip()
                chunks.append(
                    Chunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        tenant_id=tenant_id,
                        content=chunk_text,
                        embedding=[],
                        chunk_index=len(chunks),
                        token_count=estimate_token_count(chunk_text),
                        metadata={**base_meta, "semantic_distance": round(dist, 4)},
                    )
                )
                current_sentences = [next_sentence]
                current_tokens = next_tokens
            else:
                current_sentences.append(next_sentence)
                current_tokens += next_tokens

        # Append last remaining chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    tenant_id=tenant_id,
                    content=chunk_text,
                    embedding=[],
                    chunk_index=len(chunks),
                    token_count=estimate_token_count(chunk_text),
                    metadata=base_meta,
                )
            )

        return chunks
