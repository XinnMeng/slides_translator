# pptx-translator

A small Python CLI tool to read a PowerPoint `.pptx`, detect candidate text, translate likely German text to English using a free LibreTranslate-compatible API, and write a translated `.pptx` file.

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
- Translator abstraction for swappable backends.
- Default backend: free LibreTranslate-compatible API.
- Tests for extraction, replacement, and tiny end-to-end workflow.

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

## Environment variables

No required API key by default.

Optional if your LibreTranslate provider needs auth:
- `LIBRETRANSLATE_API_KEY`

## CLI usage

### Translate a deck (default de -> en)

```bash
pptx-translator demo_german_slides.pptx translated_slides.pptx
```

### Explicit language options

```bash
pptx-translator input.pptx output.pptx --source de --target en
```

### Dry run (extract JSON only)

```bash
pptx-translator demo_german_slides.pptx --dry-run --dry-run-json extracted.json
```

### Use a custom free endpoint

```bash
pptx-translator input.pptx output.pptx --libretranslate-url https://libretranslate.com/translate
```

### Optional API key

```bash
pptx-translator input.pptx output.pptx --libretranslate-api-key "$LIBRETRANSLATE_API_KEY"
```

## Demo workflow

Run the example script:

```bash
python examples/demo_workflow.py
```

This generates dry-run JSON at `examples/demo_extracted_text.json` and a translated deck at `examples/demo_translated.pptx`.

## Translation backend design

`TranslatorBackend` is an abstraction (`src/pptx_translator/translator.py`).

- `LibreTranslateTranslator` is the default implementation.
- It translates per text item using a free LibreTranslate-compatible `/translate` endpoint.
- It keeps likely-English text unchanged when source is `de`.

This makes it easy to add future backends.

## Known limitations

- Public free translation endpoints may have rate limits or availability issues.
- Run-level formatting is only partially preserved when translated text length changes.
- German-language detection is heuristic-based in this initial version.
- Some complex SmartArt/charts/embedded objects are not traversed for text.

## Running tests

```bash
pytest
```
