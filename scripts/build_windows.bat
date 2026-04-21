@echo off
setlocal

REM Build Windows desktop executable (.exe) for pptx-translator GUI

if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .[dev]

pyinstaller --clean --noconfirm --windowed --name pptx-translator-gui ^
  --collect-all argostranslate ^
  --collect-all PySide6 ^
  --hidden-import fitz ^
  --hidden-import argostranslate.package ^
  --hidden-import argostranslate.translate ^
  -m pptx_translator.gui_app

echo Build complete. See dist\pptx-translator-gui\
endlocal
