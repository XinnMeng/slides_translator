from __future__ import annotations

import json
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz")

from pptx_translator.extractors.pdf_extractor import extract_pdf_text_blocks, write_extraction_json


def _make_simple_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text((40, 60), "こんにちは")
    page.insert_text((40, 120), "第二行")
    doc.save(str(path))
    doc.close()


def test_extract_pdf_blocks_simple(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    json_path = tmp_path / "blocks.json"
    _make_simple_pdf(pdf_path)

    result = extract_pdf_text_blocks(pdf_path)
    assert result.page_count == 1
    assert len(result.pages[0].blocks) >= 1
    assert any("こんにちは" in b.text for b in result.pages[0].blocks)

    write_extraction_json(result, json_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["page_count"] == 1
    assert payload["pages"][0]["blocks"][0]["page_index"] == 0
    assert "bbox" in payload["pages"][0]["blocks"][0]
