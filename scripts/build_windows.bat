@echo off
setlocal

REM Build Windows desktop executable (.exe) for pptx-translator GUI.
REM Assumes your virtual environment is already created and dependencies installed.

where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
  echo ERROR: pyinstaller not found in PATH.
  echo Activate your venv first and install dependencies: pip install -e .[dev]
  exit /b 1
)

pyinstaller --clean --noconfirm --windowed --name pptx-translator-gui ^
  --collect-all argostranslate ^
  --collect-all PySide6 ^
  --hidden-import fitz ^
  --hidden-import argostranslate.package ^
  --hidden-import argostranslate.translate ^
  -m pptx_translator.gui_app

echo Build complete. See dist\pptx-translator-gui\
endlocal
