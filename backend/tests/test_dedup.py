"""Unit tests for SHA-256 deduplication and hash integrity."""

import tempfile
from pathlib import Path

from app.core.security import compute_file_sha256, compute_sha256


def test_sha256_byte_calculation():
    data1 = b"Contenido corporativo confidencial para RAG"
    data2 = b"Contenido corporativo confidencial para RAG"
    data3 = b"Contenido diferente"

    hash1 = compute_sha256(data1)
    hash2 = compute_sha256(data2)
    hash3 = compute_sha256(data3)

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64


def test_file_sha256_matches_content():
    content = b"Informacion de prueba en archivo de disco."
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(content)
        tmp_path = Path(f.name)

    try:
        file_hash = compute_file_sha256(tmp_path)
        byte_hash = compute_sha256(content)
        assert file_hash == byte_hash
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
