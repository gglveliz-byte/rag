"""Plain text and Markdown loader."""

from pathlib import Path
from fastapi import HTTPException, status

from app.loaders.base_loader import BaseLoader
from app.schemas.document import ExtractedDocument


class TxtLoader(BaseLoader):
    """Loads plain text (.txt) and Markdown (.md) documents with encoding normalization."""

    def supported_extensions(self) -> list[str]:
        return [".txt", ".md"]

    def extract(self, file_path: Path) -> ExtractedDocument:
        if not file_path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe.")

        content: str | None = None
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pudo decodificar el archivo de texto.",
            )

        # Normalize line endings
        normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo de texto está vacío.",
            )

        lines = normalized.split("\n")
        words = normalized.split()

        return ExtractedDocument(
            filename=file_path.name,
            file_type="txt" if file_path.suffix.lower() == ".txt" else "md",
            file_size_bytes=file_path.stat().st_size,
            content=normalized,
            metadata={
                "line_count": len(lines),
                "word_count": len(words),
            },
        )
