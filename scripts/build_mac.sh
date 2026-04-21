#!/usr/bin/env bash
set -euo pipefail

# Build macOS app bundle for pptx-translator GUI.
# Assumes your virtual environment is already created and dependencies installed.

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "ERROR: pyinstaller not found in PATH."
  echo "Activate your venv first and install dependencies: pip install -e .[dev]"
  exit 1
fi

pyinstaller --clean --noconfirm --windowed --name pptx-translator-gui \
  --collect-all argostranslate \
  --collect-all PySide6 \
  --hidden-import fitz \
  --hidden-import argostranslate.package \
  --hidden-import argostranslate.translate \
  -m pptx_translator.gui_app

echo "Build complete. See dist/pptx-translator-gui.app"
