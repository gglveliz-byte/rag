"""Abstract base class for all file format loaders."""

from abc import ABC, abstractmethod
from pathlib import Path

from app.schemas.document import ExtractedDocument


class BaseLoader(ABC):
    """Abstract base contract for document loaders."""

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractedDocument:
        """Extract plain text and structured metadata from a file.

        Args:
            file_path: Path to the target file.

        Returns:
            ExtractedDocument containing text and metadata.
        """
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of lowercase file extensions supported by this loader (e.g. ['.pdf'])."""
        pass
