from __future__ import annotations

import logging
from pathlib import Path

from ..extractors.pdf_extractor import extract_pdf_text_blocks, write_extraction_json
from ..translator import TranslatorBackend
from ..writers.pdf_to_pptx_writer import write_pdf_pages_to_pptx

logger = logging.getLogger(__name__)


def run_extract_pdf_blocks(input_pdf: Path, json_out: Path) -> dict:
    result = extract_pdf_text_blocks(input_pdf)
    write_extraction_json(result, json_out)
    return {"mode": "extract-pdf-blocks", "pages": result.page_count, "json": str(json_out)}


def run_pdf_to_pptx_translation(
    input_pdf: Path,
    output_pptx: Path,
    translator: TranslatorBackend,
    source_lang: str = "ja",
    target_lang: str = "zh-CN",
) -> dict:
    extraction = extract_pdf_text_blocks(input_pdf)

    translated_by_key: dict[tuple[int, int], str] = {}

    for page in extraction.pages:
        translated_count = 0
        for block in page.blocks:
            translated = translator.translate_text(block.text, source_lang=source_lang, target_lang=target_lang)
            translated_by_key[(block.page_index, block.block_index)] = translated
            translated_count += 1

        logger.info("Blocks translated on page %s: %s", page.page_index, translated_count)

    prs = write_pdf_pages_to_pptx(extraction.pages, translated_by_key)
    prs.save(str(output_pptx))

    return {
        "mode": "pdf-to-pptx",
        "pages": extraction.page_count,
        "translated_blocks": len(translated_by_key),
        "output": str(output_pptx),
    }
