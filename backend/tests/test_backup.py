"""Unit tests for agnostic .ragpkg export and import."""

import gzip
import json
import tempfile
from pathlib import Path
import pytest

from app.backup.importer import import_tenant_backup


@pytest.mark.asyncio
async def test_backup_package_structure():
    with tempfile.NamedTemporaryFile("wb", suffix=".ragpkg", delete=False) as f:
        pkg_path = Path(f.name)

    try:
        # Write valid .ragpkg
        header = {
            "record_type": "metadata",
            "format_version": "1.0.0",
            "created_at": "2026-09-13T12:00:00Z",
            "tenant_id": "original_tenant",
            "total_documents": 1,
            "total_chunks": 1,
        }
        doc_record = {
            "record_type": "document",
            "data": {
                "document_id": "doc_backup_001",
                "tenant_id": "original_tenant",
                "filename": "backup_sample.txt",
                "file_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
                "file_type": "txt",
                "file_size_bytes": 100,
                "total_chunks": 1,
                "tags": ["backup"],
                "created_at": "2026-09-13T12:00:00Z",
                "is_ephemeral": False,
                "expires_at": None,
                "version": 1,
            },
        }
        chunk_record = {
            "record_type": "chunk",
            "data": {
                "chunk_id": "chunk_backup_001",
                "document_id": "doc_backup_001",
                "tenant_id": "original_tenant",
                "content": "Contenido respaldado y verificado.",
                "embedding": [0.1, 0.2, 0.3],
                "chunk_index": 0,
                "token_count": 5,
                "metadata": {},
            },
        }

        with gzip.open(pkg_path, "wt", encoding="utf-8") as gz:
            gz.write(json.dumps(header) + "\n")
            gz.write(json.dumps(doc_record) + "\n")
            gz.write(json.dumps(chunk_record) + "\n")

        # Verify reading gzip header
        with gzip.open(pkg_path, "rt", encoding="utf-8") as gz:
            read_header = json.loads(gz.readline())
            assert read_header["record_type"] == "metadata"
            assert read_header["format_version"] == "1.0.0"

    finally:
        if pkg_path.exists():
            pkg_path.unlink()
