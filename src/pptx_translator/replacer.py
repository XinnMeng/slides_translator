from __future__ import annotations

import logging

from pptx.presentation import Presentation

from .models import TextItem, text_item_id

logger = logging.getLogger(__name__)


def _replace_paragraph_text(paragraph, new_text: str) -> None:
    """
    Replace paragraph text while preserving paragraph properties and first-run style.

    Strategy:
    - If there are runs, write all new text into the first run and clear the rest.
    - If there are no runs, set paragraph.text directly.
    """
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ""
    else:
        paragraph.text = new_text


def apply_translations(prs: Presentation, items: list[TextItem], translated_by_id: dict[str, str]) -> int:
    """Apply translated text back into the presentation using extracted item references."""
    applied = 0

    for item in items:
        item_key = text_item_id(item.ref)
        if item_key not in translated_by_id:
            continue

        translated_text = translated_by_id[item_key]
        if translated_text == item.text:
            continue

        slide = prs.slides[item.ref.slide_index]
        shape = slide.shapes[item.ref.shape_index]

        if item.ref.text_frame_paragraph_index is not None:
            paragraph = shape.text_frame.paragraphs[item.ref.text_frame_paragraph_index]
            _replace_paragraph_text(paragraph, translated_text)
            applied += 1
            continue

        if (
            item.ref.table_row_index is not None
            and item.ref.table_col_index is not None
            and item.ref.table_paragraph_index is not None
        ):
            cell = shape.table.rows[item.ref.table_row_index].cells[item.ref.table_col_index]
            paragraph = cell.text_frame.paragraphs[item.ref.table_paragraph_index]
            _replace_paragraph_text(paragraph, translated_text)
            applied += 1

    logger.info("Applied %s translated text items", applied)
    return applied
