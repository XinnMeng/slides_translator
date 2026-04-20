# AGENTS.md

## Project goal
Build a small Python tool that reads a PowerPoint .pptx file, detects German text in slides, translates it to English, and writes a new translated .pptx file.

## Requirements
- Use Python.
- Preserve slide layout.
- Preserve text formatting as much as possible.
- Do not rasterize slides.
- Do not depend on Microsoft PowerPoint being installed.
- Provide both a CLI and a small demo workflow.
- Keep the code simple and readable.

## Preferred architecture
- src/ for application code
- tests/ for tests
- examples/ for sample files
- requirements.txt or pyproject.toml
- README with setup and usage

## Functional requirements
- Input: .pptx file path
- Output: translated .pptx file path
- Traverse text in text boxes, placeholders, and tables
- Skip non-text shapes safely
- Support a configurable source language and target language
- Default use case: German to English
- Add a dry-run mode that exports extracted text to JSON without rewriting slides
- Add a demo script using a small sample deck

## Translation behavior
- Translate only text that is likely German
- Leave already-English text unchanged
- Preserve names, product names, acronyms, and numbers where possible
- Keep bullet structure where possible

## Quality bar
- Add unit tests for text extraction and replacement logic
- Add one integration test on a tiny sample deck
- Document known limitations clearly
