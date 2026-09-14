"""Excel (.xlsx) loader using openpyxl and pandas for structured RAG extraction."""

from pathlib import Path
import openpyxl
import pandas as pd
from fastapi import HTTPException, status

from app.loaders.base_loader import BaseLoader
from app.schemas.document import ExtractedDocument


class ExcelLoader(BaseLoader):
    """Extracts tabular data from Excel (.xlsx) workbooks into readable RAG text."""

    def supported_extensions(self) -> list[str]:
        return [".xlsx"]

    def extract(self, file_path: Path) -> ExtractedDocument:
        if not file_path.exists():
            raise FileNotFoundError(f"El archivo {file_path} no existe.")

        try:
            with pd.ExcelFile(str(file_path), engine="openpyxl") as excel_file:
                sheet_texts: list[str] = []
                sheets_summary: list[dict[str, str | int]] = []
                sheet_names = list(excel_file.sheet_names)

                for sheet_name in sheet_names:
                    try:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    except Exception:
                        continue

                    if df.empty:
                        continue

                    # Drop completely empty rows and columns
                    df = df.dropna(how="all").dropna(axis=1, how="all")
                    if df.empty:
                        continue

                    sheets_summary.append({
                        "sheet_name": sheet_name,
                        "rows": len(df),
                        "columns": len(df.columns),
                    })

                    rows_text: list[str] = [f"=== Hoja: {sheet_name} ({len(df)} filas) ==="]
                    columns = [str(col).strip() for col in df.columns]

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

                    sheet_texts.append("\n".join(rows_text))

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"No se pudo leer el archivo Excel .xlsx: {exc}",
            )

        full_content = "\n\n".join(sheet_texts)
        if not full_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo Excel no contiene datos o todas las hojas están vacías.",
            )

        return ExtractedDocument(
            filename=file_path.name,
            file_type="xlsx",
            file_size_bytes=file_path.stat().st_size,
            content=full_content,
            metadata={
                "sheet_count": len(sheet_names),
                "sheets": sheets_summary,
            },
        )

