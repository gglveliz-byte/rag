from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.core.auth import MOCK_API_KEYS_DB, hash_api_key
from app.main import app
from app.schemas.document import SearchResult
from app.vector_stores.store_manager import store_manager

client = TestClient(app)

MOCK_RESULTS = [
    SearchResult(
        chunk_id="chunk_001",
        document_id="doc_001",
        content="La política de seguridad exige autenticación multifactor.",
        score=0.92,
        source_file="politica_seguridad.pdf",
        metadata={"page_number": 4},
    )
]


def test_rag_api_invalid_key_fails():
    res = client.post(
        "/api/v1/rag/query",
        headers={"Authorization": "Bearer rke_live_invalidkey1234567890abcdef"},
        json={"query": "test query"},
    )
    assert res.status_code == 401


@patch.object(store_manager, "search", new_callable=AsyncMock)
def test_rag_api_with_guest_session(mock_search):
    mock_search.return_value = MOCK_RESULTS
    # Guests can query their own session
    res = client.post(
        "/api/v1/rag/query",
        headers={"X-Guest-Session": "session_guest_unit_test"},
        json={
            "query": "¿Cuál es la política de seguridad?",
            "top_k": 3,
            "include_formatted_context": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "query" in data
    assert "context_text" in data
    assert "chunks" in data
    assert len(data["chunks"]) == 1
    assert "politica_seguridad.pdf" in data["context_text"]
    assert "execution_time_ms" in data


@patch.object(store_manager, "search", new_callable=AsyncMock)
def test_rag_api_with_registered_api_key(mock_search):
    mock_search.return_value = MOCK_RESULTS
    # Register mock key
    raw_key = "rke_live_testdummykeyforunittesting123456"
    key_hash = hash_api_key(raw_key)
    MOCK_API_KEYS_DB[key_hash] = {
        "key_id": "key_123",
        "user_id": "user_qa",
        "name": "QA Key",
        "is_active": True,
    }

    res = client.post(
        "/api/v1/rag/query",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={"query": "proceso de backup", "top_k": 2},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "proceso de backup"
    assert len(data["chunks"]) == 1

