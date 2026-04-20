from __future__ import annotations

import json
import logging
from pathlib import Path

from pptx import Presentation

from .extractor import extract_text_items, group_items_by_slide
from .models import text_item_id
from .replacer import apply_translations
from .translator import TranslatorBackend

logger = logging.getLogger(__name__)


def run_translation(
    input_path: Path,
    output_path: Path | None,
    source_lang: str,
    target_lang: str,
    translator: TranslatorBackend,
    dry_run: bool = False,
    dry_run_json_path: Path | None = None,
) -> dict:
    prs = Presentation(str(input_path))
    items = extract_text_items(prs)
    grouped = group_items_by_slide(items)

    for slide_idx, slide_items in sorted(grouped.items()):
        logger.info("Extraction summary: slide %s has %s text items", slide_idx, len(slide_items))

    dry_payload = {
        "input_file": str(input_path),
        "source": source_lang,
        "target": target_lang,
        "count": len(items),
        "items": [item.to_json_dict() for item in items],
    }

    if dry_run:
        if dry_run_json_path:
            dry_run_json_path.write_text(json.dumps(dry_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Dry run complete with %s extracted items", len(items))
        return {"mode": "dry-run", "count": len(items), "json": str(dry_run_json_path) if dry_run_json_path else None}

    item_by_id = {text_item_id(item.ref): item for item in items}
    translated_by_id: dict[str, str] = {}
    translated_counts_by_slide: dict[int, int] = {}

    for slide_idx, slide_items in sorted(grouped.items()):
        logger.info("Translating slide %s (%s items)", slide_idx, len(slide_items))
        result = translator.translate_items(slide_items, source_lang=source_lang, target_lang=target_lang)

        for t in result.translations:
            translated_by_id[t.id] = t.translated_text
            source_item = item_by_id.get(t.id)
            if source_item is not None:
                s_idx = source_item.ref.slide_index
                translated_counts_by_slide[s_idx] = translated_counts_by_slide.get(s_idx, 0) + 1

        logger.info("Translation summary: slide %s returned %s translated items", slide_idx, len(result.translations))

    for slide_idx, slide_items in sorted(grouped.items()):
        translated_count = translated_counts_by_slide.get(slide_idx, 0)
        logger.info(
            "Translated results summary: slide %s has %s/%s translated items",
            slide_idx,
            translated_count,
            len(slide_items),
        )

    applied = apply_translations(prs, items, translated_by_id)

    if output_path is None:
        raise ValueError("output_path is required unless dry_run=True")

    prs.save(str(output_path))
    logger.info("Saved translated deck to %s", output_path)
    return {"mode": "translate", "count": len(items), "applied": applied, "output": str(output_path)}
