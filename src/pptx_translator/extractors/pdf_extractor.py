from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PdfTextBlock:
    page_index: int
    block_index: int
    bbox: tuple[float, float, float, float]
    text: str


@dataclass(frozen=True)
class PdfPageBlocks:
    page_index: int
    page_width: float
    page_height: float
    blocks: list[PdfTextBlock]


@dataclass(frozen=True)
class PdfExtractionResult:
    page_count: int
    pages: list[PdfPageBlocks]


def _clean_text(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def extract_pdf_text_blocks(pdf_path: Path) -> PdfExtractionResult:
    doc = fitz.open(str(pdf_path))
    pages: list[PdfPageBlocks] = []

    logger.info("PDF page count: %s", doc.page_count)

    for page_index in range(doc.page_count):
        page = doc.load_page(page_index)
        page_rect = page.rect

        raw_blocks = page.get_text("blocks", sort=True)
        page_blocks: list[PdfTextBlock] = []

        for block_index, block in enumerate(raw_blocks):
            x0, y0, x1, y1, text, *_rest = block
            cleaned = _clean_text(text or "")
            if not cleaned:
                continue

            page_blocks.append(
                PdfTextBlock(
                    page_index=page_index,
                    block_index=block_index,
                    bbox=(float(x0), float(y0), float(x1), float(y1)),
                    text=cleaned,
                )
            )

        if not page_blocks:
            logger.warning("Page %s has no text blocks (empty or image-only)", page_index)

        logger.info("Blocks extracted from page %s: %s", page_index, len(page_blocks))

        pages.append(
            PdfPageBlocks(
                page_index=page_index,
                page_width=float(page_rect.width),
                page_height=float(page_rect.height),
                blocks=page_blocks,
            )
        )

    return PdfExtractionResult(page_count=doc.page_count, pages=pages)


def extraction_to_json_dict(result: PdfExtractionResult) -> dict:
    return {
        "page_count": result.page_count,
        "pages": [
            {
                "page_index": page.page_index,
                "page_width": page.page_width,
                "page_height": page.page_height,
                "block_count": len(page.blocks),
                "blocks": [
                    {
                        "page_index": block.page_index,
                        "block_index": block.block_index,
                        "bbox": list(block.bbox),
                        "text": block.text,
                    }
                    for block in page.blocks
                ],
            }
            for page in result.pages
        ],
    }


def write_extraction_json(result: PdfExtractionResult, json_out: Path) -> None:
    payload = extraction_to_json_dict(result)
    json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
