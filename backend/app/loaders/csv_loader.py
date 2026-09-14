"""CSV loader using pandas with automatic encoding detection."""

from pathlib import Path
import pandas as pd
from fastapi import HTTPException, status

from app.loaders.base_loader import BaseLoader
from app.schemas.document import ExtractedDocument


class CSVLoader(BaseLoader):
    """Extracts tabular data from CSV files and formats rows for semantic search."""

    def supported_extensions(self) -> list[str]:
        return [".csv"]

    def extract(self, file_path: Path) -> ExtractedDocument:
        if not file_path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe.")

        df: pd.DataFrame | None = None
        # Try UTF-8 first, fallback to latin-1 / cp1252
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(file_path, encoding=encoding, on_bad_lines="skip")
                break
            except (UnicodeDecodeError, Exception):
                continue

        if df is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No se pudo decodificar el archivo CSV con encodings estándar (utf-8, latin-1).",
            )

        df = df.dropna(how="all").dropna(axis=1, how="all")
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo CSV está vacío.",
            )

        columns = [str(c).strip() for c in df.columns]
        rows_text: list[str] = [f"=== CSV: {file_path.name} ({len(df)} filas, {len(columns)} columnas) ==="]

        for row_idx, row in df.iterrows():
            row_items = []
            for col_name in columns:
                val = row[col_name]
                if pd.notna(val):
                    val_str = str(val).strip()
                    if val_str:
                        row_items.append(f"{col_name}: {val_str}")
            if row_items:
                rows_text.append(f"[Fila {row_idx + 1}] " + " | ".join(row_items))

        content = "\n".join(rows_text)

        return ExtractedDocument(
            filename=file_path.name,
            file_type="csv",
            file_size_bytes=file_path.stat().st_size,
            content=content,
            metadata={
                "row_count": len(df),
                "columns": columns,
            },
        )
