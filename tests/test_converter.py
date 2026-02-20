from pathlib import Path

import fitz
import pytest

from roop_pdfmd.core.converter import ConversionError, Converter
from roop_pdfmd.core.models import AppSettings


def _make_text_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello from text layer")
    doc.save(path)
    doc.close()


def _make_two_page_text_pdf(path: Path) -> None:
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((72, 72), "First page text layer content.")
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Second page text layer content.")
    doc.save(path)
    doc.close()


def test_converter_extracts_text_layer(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    out_dir = tmp_path / "out"
    _make_text_pdf(pdf_path)

    converter = Converter()
    result = converter.convert(pdf_path, out_dir, AppSettings())

    assert result.total_pages == 1
    assert result.extracted_pages == 1
    assert result.ocr_pages == 0

    md_text = result.markdown_path.read_text(encoding="utf-8")
    txt_text = result.text_path.read_text(encoding="utf-8")

    assert "--- Page 1 ---" in md_text
    assert "Hello from text layer" in md_text
    assert txt_text == md_text
    assert result.metadata_path.exists()


def test_converter_raises_for_missing_pdf(tmp_path: Path) -> None:
    converter = Converter()
    with pytest.raises(ConversionError):
        converter.convert(tmp_path / "missing.pdf", tmp_path, AppSettings())


def test_converter_page_callback_streams_per_page_chunks(tmp_path: Path) -> None:
    pdf_path = tmp_path / "two_pages.pdf"
    out_dir = tmp_path / "out"
    _make_two_page_text_pdf(pdf_path)

    converter = Converter()
    chunks: list[str] = []

    def _on_page_chunk(_page_result, markdown_chunk: str, _text_chunk: str) -> None:
        chunks.append(markdown_chunk)

    result = converter.convert(
        pdf_path,
        out_dir,
        AppSettings(),
        page_callback=_on_page_chunk,
    )

    assert result.processed_pages == 2
    assert len(chunks) == 2
    assert "--- Page 1 ---" in chunks[0]
    assert "--- Page 2 ---" not in chunks[0]
    assert "--- Page 2 ---" in chunks[1]
