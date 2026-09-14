"""Unit tests for document loaders and LoaderFactory router."""

import tempfile
from pathlib import Path
import pandas as pd
import pytest

from app.loaders.csv_loader import CSVLoader
from app.loaders.excel_loader import ExcelLoader
from app.loaders.loader_factory import loader_factory
from app.loaders.txt_loader import TxtLoader


def test_txt_loader():
    loader = TxtLoader()
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Line 1 of test document.\nLine 2 with important RAG facts.\n\nParagraph 2.")
        tmp_path = Path(f.name)

    try:
        extracted = loader.extract(tmp_path)
        assert extracted.file_type == "txt"
        assert "Line 1" in extracted.content
        assert extracted.metadata["word_count"] > 5
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_csv_loader():
    loader = CSVLoader()
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("producto,precio,stock\nLaptop,1200,10\nMonitor,300,25\n")
        tmp_path = Path(f.name)

    try:
        extracted = loader.extract(tmp_path)
        assert extracted.file_type == "csv"
        assert "Laptop" in extracted.content
        assert "precio: 1200" in extracted.content
        assert extracted.metadata["row_count"] == 2
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_excel_loader():
    loader = ExcelLoader()
    df = pd.DataFrame({
        "Empleado": ["Alice", "Bob"],
        "Departamento": ["Seguridad", "I+D"],
    })
    tmp = tempfile.NamedTemporaryFile("wb", suffix=".xlsx", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()

    try:
        df.to_excel(str(tmp_path), index=False)
        extracted = loader.extract(tmp_path)
        assert extracted.file_type == "xlsx"
        assert "Empleado: Alice" in extracted.content
        assert "Departamento: Seguridad" in extracted.content
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_loader_factory_dispatcher():
    p_txt = Path("sample.txt")
    p_csv = Path("sample.csv")
    p_pdf = Path("sample.pdf")
    p_doc = Path("sample.docx")

    assert isinstance(loader_factory.get_loader(p_txt), TxtLoader)
    assert isinstance(loader_factory.get_loader(p_csv), CSVLoader)

    with pytest.raises(Exception):
        loader_factory.get_loader(Path("unsupported.xyz"))
