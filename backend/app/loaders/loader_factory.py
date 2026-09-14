"""Loader factory and format router for automatic loader selection."""

from pathlib import Path
from fastapi import HTTPException, status

from app.loaders.base_loader import BaseLoader
from app.loaders.csv_loader import CSVLoader
from app.loaders.docx_loader import DocxLoader
from app.loaders.excel_loader import ExcelLoader
from app.loaders.pdf_loader import PDFLoader
from app.loaders.txt_loader import TxtLoader
from app.schemas.document import ExtractedDocument


class LoaderFactory:
    """Registry and dispatcher for document loaders based on file extensions."""

    def __init__(self) -> None:
        self._loaders: list[BaseLoader] = [
            PDFLoader(),
            DocxLoader(),
            ExcelLoader(),
            CSVLoader(),
            TxtLoader(),
        ]
        self._extension_map: dict[str, BaseLoader] = {}
        for loader in self._loaders:
            for ext in loader.supported_extensions():
                self._extension_map[ext.lower()] = loader

    def get_loader(self, file_path: Path) -> BaseLoader:
        """Find appropriate loader for given file extension.

        Args:
            file_path: Path to file.

        Returns:
            Matching BaseLoader implementation.

        Raises:
            HTTPException: If file extension is unsupported.
        """
        ext = file_path.suffix.lower()
        loader = self._extension_map.get(ext)
        if not loader:
            supported = ", ".join(sorted(self._extension_map.keys()))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No hay loader disponible para la extensión '{ext}'. Formatos soportados: {supported}",
            )
        return loader

    def extract(self, file_path: Path) -> ExtractedDocument:
        """Route to appropriate loader and extract document content.

        Args:
            file_path: Path to target file.

        Returns:
            ExtractedDocument instance.
        """
        loader = self.get_loader(file_path)
        return loader.extract(file_path)


# Singleton factory instance
loader_factory = LoaderFactory()
