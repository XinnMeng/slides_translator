#!/usr/bin/env bash
set -euo pipefail

# Build macOS app bundle for pptx-translator GUI

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]

pyinstaller --clean --noconfirm --windowed --name pptx-translator-gui \
  --collect-all argostranslate \
  --collect-all PySide6 \
  --hidden-import fitz \
  --hidden-import argostranslate.package \
  --hidden-import argostranslate.translate \
  -m pptx_translator.gui_app

echo "Build complete. See dist/pptx-translator-gui.app"
