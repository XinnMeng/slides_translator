from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .pipeline import run_translation
from .translator import OpenAIResponsesTranslator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Translate likely German text in PPTX files to English")
    parser.add_argument("input", type=Path, help="Input .pptx path")
    parser.add_argument("output", nargs="?", type=Path, help="Output translated .pptx path")
    parser.add_argument("--source", default="de", help="Source language code (default: de)")
    parser.add_argument("--target", default="en", help="Target language code (default: en)")
    parser.add_argument("--dry-run", action="store_true", help="Extract text candidates to JSON and do not modify deck")
    parser.add_argument("--dry-run-json", type=Path, default=Path("dry_run_text.json"), help="Path for dry-run JSON")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model for translation")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    if not args.input.exists():
        parser.error(f"Input file does not exist: {args.input}")

    if not args.dry_run and args.output is None:
        parser.error("output path is required unless --dry-run is set")

    try:
        translator = OpenAIResponsesTranslator(model=args.model)
        result = run_translation(
            input_path=args.input,
            output_path=args.output,
            source_lang=args.source,
            target_lang=args.target,
            translator=translator,
            dry_run=args.dry_run,
            dry_run_json_path=args.dry_run_json,
        )
        logging.getLogger(__name__).info("Completed: %s", result)
    except Exception as exc:  # graceful top-level handling
        logging.getLogger(__name__).exception("Translation failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
