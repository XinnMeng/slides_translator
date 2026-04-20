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

For offline translation, install Argos language packages for your language pair.

### Option A (recommended): auto-install from CLI

This will download/install a missing package the first time:

```bash
pptx-translator test-translation --text "こんにちは" --source ja --target zh-CN --backend offline_argos --argos-auto-install-package
```

### Option B: install a specific package manually

Run this Python snippet to install a specific pair (example: `ja -> zh`):

```bash
python - <<'EOF'
import argostranslate.package

source = "ja"
target = "zh"

argostranslate.package.update_package_index()
pkgs = argostranslate.package.get_available_packages()
match = next((p for p in pkgs if p.from_code == source and p.to_code == target), None)
if not match:
    raise SystemExit(f"No Argos package found for {source}->{target}")
path = match.download()
argostranslate.package.install_from_path(path)
print(f"Installed Argos package: {source}->{target}")
EOF
```

You can change `source` / `target` for other pairs, e.g.:
- `de -> en`
- `ja -> zh`

> Note: `zh-CN` is normalized to `zh` for Argos package matching in this project.

## Argos direct + pivot fallback

When using Argos backend, translation resolution is:
1. Try direct model: `source -> target` (for example `ja -> zh`).
2. If direct model is missing, automatically fall back to pivot path (default pivot: `en`):
   - `ja -> en -> zh`

You can configure pivot language from CLI:

```bash
pptx-translator pdf-to-pptx input.pdf output.pptx --source ja --target zh --backend offline_argos --argos-pivot-lang en
```

The logs will show either:
- `Using direct model: ja -> zh`
- `Direct model not found, using pivot: ja -> en -> zh`

If required models are missing (`ja -> en` or `en -> zh`), use `--argos-auto-install-package` or install them manually.

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
