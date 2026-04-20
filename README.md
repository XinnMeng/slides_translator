# pptx-translator

A small Python CLI tool to read a PowerPoint `.pptx`, detect candidate text, translate likely German text to English, and write a translated `.pptx` file.

It uses `python-pptx` only (no Microsoft PowerPoint installation required).

## Features

- Traverses slide text in:
  - text boxes
  - placeholders/text-frame shapes
  - table cells
- Safely skips unsupported/non-text shapes.
- Preserves slide layout and keeps formatting as much as possible (run style of first run is preserved during replacement).
- Configurable language pair with defaults:
  - `--source de`
  - `--target en`
- Dry-run mode to export extracted text items to JSON without modifying slides.
- Backend abstraction with multiple translators:
  - `argos` (default, offline/local)
  - `libretranslate` (optional custom URL backend)
- Dedicated `test-translation` command to verify one sentence before processing slides.

## Why LibreTranslate returned HTTP 400

Some LibreTranslate-compatible deployments expect `application/x-www-form-urlencoded` payloads rather than JSON payloads.

This project now:
- tries `form` payload first,
- falls back to JSON payload,
- logs full failure response body and status code for debugging.

## Project structure

- `src/pptx_translator/` – package code
- `tests/` – unit and integration tests
- `examples/` – demo workflow and dry-run output target
- `demo_german_slides.pptx` – sample input deck

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# for tests
pip install -e .[dev]
```

### Argos Translate language package setup (de -> en)

Argos backend is local/offline once language packages are installed.

You can either:
1. install packages yourself in advance, or
2. run CLI with `--argos-auto-install-package` to allow automatic package download/install.

Example preflight test (recommended):

```bash
pptx-translator test-translation --text "Guten Morgen" --source de --target en --backend argos --argos-auto-install-package
```

## Environment variables

Optional if your LibreTranslate provider needs auth:
- `LIBRETRANSLATE_API_KEY`

## CLI usage

### 1) Test one sentence first (recommended)

```bash
pptx-translator test-translation --text "Guten Morgen" --source de --target en --backend argos
```

### 2) Translate a deck with default offline backend (Argos)

```bash
pptx-translator translate demo_german_slides.pptx translated_slides.pptx
```

### 3) Validate one sentence before slide processing

```bash
pptx-translator translate input.pptx output.pptx --validate-text "Guten Morgen"
```

### 4) Dry run (extract JSON only)

```bash
pptx-translator translate demo_german_slides.pptx out.pptx --dry-run --dry-run-json extracted.json
```

### 5) Use LibreTranslate custom URL backend (optional)

```bash
pptx-translator translate input.pptx output.pptx \
  --backend libretranslate \
  --libretranslate-url https://libretranslate.com/translate
```

### 6) LibreTranslate with API key

```bash
pptx-translator translate input.pptx output.pptx \
  --backend libretranslate \
  --libretranslate-api-key "$LIBRETRANSLATE_API_KEY"
```

## Demo workflow

Run the example script:

```bash
python examples/demo_workflow.py
```

This script demonstrates:
- dry-run extraction,
- single-sentence backend test,
- full deck translation.

## Translation backend design

`TranslatorBackend` is the abstraction in `src/pptx_translator/translator.py`.

Implemented backends:
- `ArgosTranslateBackend` (default): local/offline translation with optional package auto-install.
- `LibreTranslateBackend` (optional): custom URL HTTP translation.

## Known limitations

- Argos translation quality depends on installed language package.
- Public free HTTP translation endpoints may rate limit or require API keys.
- Run-level formatting is only partially preserved when translated text length changes.
- German-language detection is heuristic-based in this initial version.
- Some complex SmartArt/charts/embedded objects are not traversed for text.

## Running tests

```bash
pytest
```
