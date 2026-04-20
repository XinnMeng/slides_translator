# pptx-translator

A Python CLI tool for:
1. translating text in `.pptx` slides, and
2. converting **digital PDFs** into translated `.pptx` slides (one output slide per PDF page).

It does not require Microsoft PowerPoint.

## Features

### PPTX -> PPTX pipeline
- Traverses text in text boxes, placeholders/text-frame shapes, and table cells.
- Preserves layout and formatting approximately.
- Per-slide extraction/translation/replacement logging.

### PDF -> PPTX pipeline (new)
- Uses **PyMuPDF (`fitz`)** with `page.get_text("blocks", sort=True)`.
- Extracts block text and bounding boxes per page.
- Creates one blank PPTX slide per PDF page.
- Maps PDF coordinates to slide coordinates (approximate layout in v1).
- Translates each text block using the **offline Argos backend** (default for this command).
- Dry-run extraction command to JSON.

## Important limitation

- v1 supports **digital PDFs only** (text-selectable PDFs).
- Scanned/image-only PDFs are not OCR’d in this version.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# tests
pip install -e .[dev]
```

Dependencies include:
- `python-pptx`
- `argostranslate`
- `PyMuPDF`

## Argos language package setup

For offline translation, install Argos language packages for your pair.

For example (ja -> zh):

```bash
pptx-translator test-translation --text "こんにちは" --source ja --target zh-CN --backend offline_argos --argos-auto-install-package
```

`zh-CN` is normalized to `zh` for Argos package matching.

## CLI commands

### 1) Translate PPTX

```bash
pptx-translator translate input.pptx output.pptx --source de --target en --backend argos
```

### 2) Test translation sentence

```bash
pptx-translator test-translation --text "Guten Morgen" --source de --target en --backend argos
```

### 3) Convert digital PDF to translated PPTX (default ja -> zh-CN)

```bash
pptx-translator pdf-to-pptx input.pdf output.pptx --backend offline_argos
```

Explicit language pair:

```bash
pptx-translator pdf-to-pptx input.pdf output.pptx --source ja --target zh-CN --backend offline_argos
```

### 4) Dry-run: extract PDF blocks to JSON

```bash
pptx-translator extract-pdf-blocks input.pdf --json-out blocks.json
```

JSON includes:
- page index
- block index
- bbox
- original text

## Logging

The PDF pipeline logs:
- page count
- blocks extracted per page
- blocks translated per page
- text boxes inserted per slide
- warnings for empty/image-only pages

## Known limitations

- PDF layout preservation is approximate in v1.
- Font/style matching from PDF is not preserved exactly.
- Very fragmented PDF text blocks may still require manual cleanup.
- Scanned PDFs are not supported in this version.

## Tests

```bash
pytest
```

Added tests cover:
- PDF text block extraction
- multi-page PDF -> PPTX conversion
- output PPTX slide count equals input PDF page count
- translated Chinese-like text appears in generated PPTX
