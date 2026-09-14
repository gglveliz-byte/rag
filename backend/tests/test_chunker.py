"""Unit tests for semantic chunking and text segmentation."""

import pytest

from app.chunking.semantic_chunker import SemanticChunker, estimate_token_count, split_into_sentences
from app.embeddings.mock_embedding import MockEmbeddingService


def test_split_into_sentences():
    text = "Primera oración de prueba. Segunda oración que continúa la idea; tercera parte con punto y coma. ¿Cuarta pregunta?"
    sentences = split_into_sentences(text)
    assert len(sentences) >= 3


def test_estimate_token_count():
    text = "Cinco palabras en esta frase"
    tokens = estimate_token_count(text)
    assert tokens >= 5


@pytest.mark.asyncio
async def test_semantic_chunker_execution():
    embedder = MockEmbeddingService(dimension=128)
    chunker = SemanticChunker(
        embedding_service=embedder,
        min_tokens=10,
        max_tokens=60,
        similarity_threshold_percentile=80.0,
    )

    sample_doc = (
        "El sistema RAG procesa documentos empresariales de manera modular. "
        "Permite indexar contenido vectorial con Alibaba DashScope text-embedding-v3. "
        "La persistencia desacoplada en PostgreSQL o MongoDB garantiza soberanía de datos.\n\n"
        "Por otro lado, la arquitectura de microservicios en Kubernetes escala horizontalmente. "
        "Los pods ejecutan workers que consumen colas de RabbitMQ. "
        "Las métricas de Prometheus y Grafana monitorean latencia y throughput."
    )

    chunks = await chunker.chunk(
        text=sample_doc,
        document_id="doc_test_123",
        tenant_id="tenant_alpha",
        metadata={"category": "architecture"},
    )

    assert len(chunks) >= 1
    for i, c in enumerate(chunks):
        assert c.document_id == "doc_test_123"
        assert c.tenant_id == "tenant_alpha"
        assert c.chunk_index == i
        assert len(c.content) > 0
