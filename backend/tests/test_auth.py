"""Unit tests for authentication, JWT and API Key endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.core.auth import (
    create_access_token,
    decode_access_token,
    generate_api_key,
    hash_password,
    verify_password,
)
from app.main import app

client = TestClient(app)


def test_password_hashing():
    pwd = "secretpassword123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_token_roundtrip():
    payload = {"sub": "user_test_123", "email": "test@example.com"}
    token = create_access_token(payload)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "user_test_123"
    assert decoded["email"] == "test@example.com"


def test_api_key_generation():
    raw, key_hash, masked = generate_api_key()
    assert raw.startswith("rke_live_")
    assert len(key_hash) == 64  # SHA-256
    assert masked.startswith("rke_live_")
    assert "..." in masked


def test_register_and_login_flow():
    email = "developer@enterprise.com"
    pwd = "securepassword99"

    # 1. Register
    reg_res = client.post("/api/auth/register", json={"email": email, "password": pwd})
    assert reg_res.status_code == 200
    token_data = reg_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 2. Duplicate registration should 409
    dup_res = client.post("/api/auth/register", json={"email": email, "password": pwd})
    assert dup_res.status_code == 409

    # 3. Login
    login_res = client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 4. Create API Key
    headers = {"Authorization": f"Bearer {token}"}
    key_res = client.post("/api/auth/api-keys", json={"name": "LangChain Production"}, headers=headers)
    assert key_res.status_code == 200
    key_data = key_res.json()
    assert "raw_key" in key_data
    assert key_data["raw_key"].startswith("rke_live_")

    # 5. List API Keys
    list_res = client.get("/api/auth/api-keys", headers=headers)
    assert list_res.status_code == 200
    keys = list_res.json()
    assert len(keys) >= 1
