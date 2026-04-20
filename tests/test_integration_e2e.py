from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from pptx_translator.extractor import extract_text_items
from pptx_translator.models import Translation, TranslationBatchResult, text_item_id
from pptx_translator.pipeline import run_translation
from pptx_translator.translator import TranslatorBackend


class FakeTranslator(TranslatorBackend):
    def translate_items(self, items, source_lang: str, target_lang: str) -> TranslationBatchResult:
        out: list[Translation] = []
        for item in items:
            replacement = {
                "Hallo": "Hello",
                "Welt": "World",
            }
            text = item.text
            for src, dst in replacement.items():
                text = text.replace(src, dst)
            out.append(Translation(id=text_item_id(item.ref), translated_text=text))
        return TranslationBatchResult(translations=out)


def test_tiny_end_to_end(tmp_path: Path) -> None:
    in_file = tmp_path / "in.pptx"
    out_file = tmp_path / "out.pptx"

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    box = slide.shapes.add_textbox(left=0, top=0, width=2_000_000, height=1_000_000)
    box.text_frame.paragraphs[0].text = "Hallo Welt"
    prs.save(in_file)

    result = run_translation(
        input_path=in_file,
        output_path=out_file,
        source_lang="de",
        target_lang="en",
        translator=FakeTranslator(),
        dry_run=False,
    )

    assert result["mode"] == "translate"
    assert result["applied"] == 1

    out_prs = Presentation(str(out_file))
    texts = [item.text for item in extract_text_items(out_prs)]
    assert "Hello World" in texts
