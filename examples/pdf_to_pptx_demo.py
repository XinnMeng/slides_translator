"""Demo for digital PDF -> translated PPTX.

Usage:
  python examples/pdf_to_pptx_demo.py input.pdf output.pptx
"""

from __future__ import annotations

import sys
from pathlib import Path

from pptx_translator.pipelines.pdf_to_pptx_pipeline import run_pdf_to_pptx_translation
from pptx_translator.translator import build_backend


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python examples/pdf_to_pptx_demo.py <input.pdf> <output.pptx>")

    input_pdf = Path(sys.argv[1])
    output_pptx = Path(sys.argv[2])

    translator = build_backend(
        backend="offline_argos",
        libretranslate_url="https://libretranslate.com/translate",
        libretranslate_api_key=None,
        argos_auto_install=True,
    )

    result = run_pdf_to_pptx_translation(
        input_pdf=input_pdf,
        output_pptx=output_pptx,
        translator=translator,
        source_lang="ja",
        target_lang="zh-CN",
    )
    print(result)


if __name__ == "__main__":
    main()
