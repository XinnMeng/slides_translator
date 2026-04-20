"""Small demo flow for pptx-translator.

Usage:
  python examples/demo_workflow.py

This script runs dry-run extraction on the repository sample deck.
"""

from pathlib import Path

from pptx_translator.pipeline import run_translation
from pptx_translator.translator import LibreTranslateTranslator

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_IN = ROOT / "demo_german_slides.pptx"
DRY_JSON = ROOT / "examples" / "demo_extracted_text.json"
OUT_FILE = ROOT / "examples" / "demo_translated.pptx"


def main() -> None:
    print("Running dry-run extraction...")
    run_translation(
        input_path=SAMPLE_IN,
        output_path=None,
        source_lang="de",
        target_lang="en",
        translator=LibreTranslateTranslator(),
        dry_run=True,
        dry_run_json_path=DRY_JSON,
    )
    print(f"Wrote dry-run JSON: {DRY_JSON}")

    print("Running free translation with LibreTranslate endpoint...")
    run_translation(
        input_path=SAMPLE_IN,
        output_path=OUT_FILE,
        source_lang="de",
        target_lang="en",
        translator=LibreTranslateTranslator(),
        dry_run=False,
    )
    print(f"Wrote translated deck: {OUT_FILE}")


if __name__ == "__main__":
    main()
