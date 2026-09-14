"""File security, validation, sanitization and hashing utilities."""

import hashlib
import re
from pathlib import Path
from fastapi import HTTPException, UploadFile, status

ALLOWED_EXTENSIONS: set[str] = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".txt",
    ".md",
}

MIME_TYPE_MAPPING: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "text/csv": ".csv",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and invalid characters.

    Args:
        filename: Raw incoming filename.

    Returns:
        Safe filename string.
    """
    clean_name = Path(filename).name
    # Keep alphanumeric, dots, underscores, dashes
    clean_name = re.sub(r"[^\w\.\-\_]", "_", clean_name)
    return clean_name or "uploaded_file"


def validate_file_extension(filename: str) -> str:
    """Check if file extension is supported.

    Args:
        filename: Filename with extension.

    Returns:
        Clean lowercase extension including dot.

    Raises:
        HTTPException: If extension is not allowed.
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de archivo '{ext}' no soportado. Formatos válidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    return ext


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hash of byte content.

    Args:
        content: Binary content of file.

    Returns:
        Hexadecimal SHA-256 digest.
    """
    hasher = hashlib.sha256()
    hasher.update(content)
    return hasher.hexdigest()


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file on disk reading in chunks.

    Args:
        file_path: Path to file.

    Returns:
        Hexadecimal SHA-256 digest.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
