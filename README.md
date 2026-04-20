# pptx-translator

A small Python CLI tool to read a PowerPoint `.pptx`, detect candidate text, translate likely German text to English using the OpenAI Responses API, and write a translated `.pptx` file.

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
- Default backend: OpenAI Responses API (batched by slide).
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

- `OPENAI_API_KEY` (required for real translation calls)

Example:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

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

### Choose model and logging level

```bash
pptx-translator input.pptx output.pptx --model gpt-4.1-mini --log-level DEBUG
```

## Demo workflow

Run the example script:

```bash
python examples/demo_workflow.py
```

This generates dry-run JSON at `examples/demo_extracted_text.json`.

## Translation backend design

`TranslatorBackend` is an abstraction (`src/pptx_translator/translator.py`).

- `OpenAIResponsesTranslator` is the default implementation.
- It sends batched text items (per slide) and requests structured JSON output:
  - `translations[]`
  - each with `{ id, translated_text }`

This makes it easy to add future backends.

## Known limitations

- Run-level formatting is only partially preserved when translated text length changes.
- German-language detection is instruction-based in the model prompt (no separate local classifier yet).
- Some complex SmartArt/charts/embedded objects are not traversed for text.

## Running tests

```bash
pytest
```
