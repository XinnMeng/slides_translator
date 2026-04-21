# PPTX Translator Desktop App

A cross-platform desktop application (Windows + macOS) for translating:
- **PowerPoint (.pptx) -> translated .pptx**
- **Digital PDF -> translated .pptx** (one slide per PDF page)

The app is designed for non-technical users with a GUI, while keeping the existing core translation pipelines reusable for developers.

---

## 1) Project overview

### What the software does
- Translates text from PowerPoint files and writes a new translated PowerPoint.
- Extracts text blocks from digital PDFs, translates them, and creates a PPTX output with approximate layout.

### Supported modes
1. **PPTX translate**
   - input: `.pptx`
   - output: `.pptx`
2. **PDF to translated PPTX**
   - input: digital (text-selectable) `.pdf`
   - output: `.pptx`

### Supported platforms
- Windows (primary end-user target)
- macOS (same codebase)

### Current limitations
- PDF mode supports **digital PDFs only** (not scanned OCR PDFs).
- PDF layout is approximate in v1 (block-level textbox mapping).
- Translation quality depends on available Argos language models.

---

## 2) End-user usage (GUI)

### Launch the GUI
After install:

```bash
pptx-translator-gui
```

Or from source:

```bash
python gui_app.py
```

### In the app
1. Select **Mode**:
   - `PPTX translate`
   - `PDF to translated PPTX`
2. Choose **Input file**.
3. Choose **Output file** (`.pptx`).
4. Choose **Source language** and **Target language**.
5. Keep backend as `offline_argos` (default recommended).
6. (Optional) check **Auto-install missing Argos models**.
7. Click **Translate**.

### If a model is missing
- The GUI shows a clear message in logs/error popup.
- If auto-install is enabled, app attempts to install missing Argos model pairs.
- If direct pair is missing, backend can use pivot fallback (default: `en`).

---

## 3) Developer setup

### Python version
- Python **3.10+**

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -e .[dev]
```

### Run GUI locally

```bash
python gui_app.py
```

or

```bash
pptx-translator-gui
```

---

## 4) Windows build instructions (.exe)

> Build Windows executable on **Windows**.

### Step-by-step
1. Open `cmd.exe` (or PowerShell) in project root.
2. Run:

```bat
scripts\build_windows.bat
```

### What the script does
- Creates `.venv` if missing
- Installs dependencies + PyInstaller
- Builds a windowed executable (no console)

### Output location
- `dist\pptx-translator-gui\` (contains `pptx-translator-gui.exe` and bundled files)

### Common issues
- Missing build tools / antivirus quarantine of `.exe`
- Missing Argos model at runtime (enable auto-install or install manually)
- Packaging misses resources: rebuild using `packaging/pyinstaller_gui.spec`

---

## 5) macOS build instructions (.app)

> Build macOS app on **macOS**.

### Run directly from Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
python gui_app.py
```

### Optional app packaging

```bash
./scripts/build_mac.sh
```

### Output location
- `dist/pptx-translator-gui.app`

### Common issues
- macOS Gatekeeper warning for unsigned app
- Missing Argos model at runtime
- App bundle missing resources (use spec file and rebuild)

---

## 6) Notes on cross-platform packaging

- A Windows `.exe` **cannot run on macOS**.
- A macOS `.app` **must be built on macOS**.
- A Windows executable **must be built on Windows**.

---

## 7) Troubleshooting

### Missing Argos language model
- Enable **Auto-install missing Argos models** in GUI.
- Or preinstall models manually.

### Unsupported language pair
- Argos may not have that direct pair.
- App automatically tries pivot fallback (`source -> en -> target`) when possible.

### PDF has no extractable text
- Likely scanned/image-only PDF.
- v1 does not include OCR.

### App opens but translation fails
- Check log/status panel for details.
- Verify language pair and model availability.
- Verify input/output file paths and write permissions.

### Packaged app cannot find resources
- Rebuild with scripts and/or `packaging/pyinstaller_gui.spec`.
- Ensure dependencies were installed in build environment.

### macOS security warning for unsigned app
- Right-click app -> Open, or allow in Security settings.

---

## 8) Example workflows

### A) German PPTX to English
- Mode: `PPTX translate`
- Source: `de`
- Target: `en`
- Backend: `offline_argos`

### B) Japanese digital PDF to Chinese PPTX
- Mode: `PDF to translated PPTX`
- Source: `ja`
- Target: `zh-CN`
- Backend: `offline_argos`

---

## CLI (still available for developers)

```bash
# PPTX workflow
pptx-translator translate input.pptx output.pptx --source de --target en --backend offline_argos

# PDF workflow
pptx-translator pdf-to-pptx input.pdf output.pptx --source ja --target zh-CN --backend offline_argos

# PDF extraction dry-run
pptx-translator extract-pdf-blocks input.pdf --json-out blocks.json
```

---

## Repository structure (high level)

- `src/pptx_translator/` core logic + CLI
- `src/pptx_translator/gui/` desktop UI + background worker
- `scripts/` platform build scripts
- `packaging/` optional pyinstaller spec
- `tests/` automated tests
