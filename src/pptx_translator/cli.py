from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from .pipeline import run_translation
from .translator import build_backend


def _add_backend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend",
        choices=["argos", "libretranslate"],
        default="argos",
        help="Translation backend (default: argos, offline)",
    )
    parser.add_argument(
        "--libretranslate-url",
        default="https://libretranslate.com/translate",
        help="LibreTranslate-compatible /translate endpoint (used when --backend libretranslate)",
    )
    parser.add_argument(
        "--libretranslate-api-key",
        default=os.getenv("LIBRETRANSLATE_API_KEY"),
        help="Optional API key for LibreTranslate service",
    )
    parser.add_argument(
        "--argos-auto-install-package",
        action="store_true",
        help="Allow Argos backend to download/install missing language package",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Translate likely German text in PPTX files to English")
    subparsers = parser.add_subparsers(dest="command", required=True)

    translate_parser = subparsers.add_parser("translate", help="Translate a PPTX file")
    translate_parser.add_argument("input", type=Path, help="Input .pptx path")
    translate_parser.add_argument("output", type=Path, help="Output translated .pptx path")
    translate_parser.add_argument("--source", default="de", help="Source language code (default: de)")
    translate_parser.add_argument("--target", default="en", help="Target language code (default: en)")
    translate_parser.add_argument("--dry-run", action="store_true", help="Extract text candidates to JSON and do not modify deck")
    translate_parser.add_argument("--dry-run-json", type=Path, default=Path("dry_run_text.json"), help="Path for dry-run JSON")
    translate_parser.add_argument(
        "--validate-text",
        default=None,
        help="Optional sentence to test translation before processing slides",
    )
    _add_backend_args(translate_parser)

    test_parser = subparsers.add_parser("test-translation", help="Test single-sentence translation")
    test_parser.add_argument("--text", required=True, help="Sentence to translate")
    test_parser.add_argument("--source", default="de", help="Source language code (default: de)")
    test_parser.add_argument("--target", default="en", help="Target language code (default: en)")
    _add_backend_args(test_parser)

    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    try:
        translator = build_backend(
            backend=args.backend,
            libretranslate_url=args.libretranslate_url,
            libretranslate_api_key=args.libretranslate_api_key,
            argos_auto_install=args.argos_auto_install_package,
        )

        if args.command == "test-translation":
            translated = translator.translate_text(args.text, source_lang=args.source, target_lang=args.target)
            print(translated)
            return 0

        if args.command == "translate":
            if not args.input.exists():
                parser.error(f"Input file does not exist: {args.input}")

            if args.validate_text:
                translated = translator.translate_text(args.validate_text, source_lang=args.source, target_lang=args.target)
                logging.getLogger(__name__).info(
                    "Validation translation succeeded: %r -> %r",
                    args.validate_text,
                    translated,
                )

            output_path = None if args.dry_run else args.output
            result = run_translation(
                input_path=args.input,
                output_path=output_path,
                source_lang=args.source,
                target_lang=args.target,
                translator=translator,
                dry_run=args.dry_run,
                dry_run_json_path=args.dry_run_json,
            )
            logging.getLogger(__name__).info("Completed: %s", result)
            return 0

        parser.error(f"Unsupported command: {args.command}")
    except Exception as exc:  # graceful top-level handling
        logging.getLogger(__name__).exception("Translation failed: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
