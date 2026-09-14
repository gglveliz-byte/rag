"""PDF loader using PyMuPDF (fitz) with page-level tracking."""

from pathlib import Path
import fitz  # PyMuPDF
from fastapi import HTTPException, status

from app.loaders.base_loader import BaseLoader
from app.schemas.document import ExtractedDocument


class PDFLoader(BaseLoader):
    """Extracts text and metadata from PDF files using PyMuPDF."""

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def extract(self, file_path: Path) -> ExtractedDocument:
        if not file_path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe.")

        try:
            doc = fitz.open(str(file_path))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"No se pudo leer el archivo PDF: {exc}",
            )

        if doc.is_encrypted:
            try:
                # Try empty password
                doc.authenticate("")
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo PDF está protegido con contraseña y no se puede procesar.",
                )

        full_text_parts: list[str] = []
        pages_metadata: list[dict[str, int | str]] = []

        total_pages = len(doc)
        for page_num in range(total_pages):
            page = doc[page_num]
            page_text = page.get_text("text").strip()
            if page_text:
                full_text_parts.append(f"[Página {page_num + 1}]\n{page_text}")
                pages_metadata.append({
                    "page_number": page_num + 1,
                    "char_count": len(page_text),
                })

        # Extract PDF metadata if available
        meta = doc.metadata or {}
        pdf_metadata = {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "total_pages": total_pages,
            "pages_with_text": len(pages_metadata),
        }

        doc.close()

        combined_content = "\n\n".join(full_text_parts)
        if not combined_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo PDF no contiene texto extraíble (puede estar compuesto únicamente de imágenes escaneadas).",
            )

        return ExtractedDocument(
            filename=file_path.name,
            file_type="pdf",
            file_size_bytes=file_path.stat().st_size,
            content=combined_content,
            metadata=pdf_metadata,
        )
