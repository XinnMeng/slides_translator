# Build with: pyinstaller packaging/pyinstaller_gui.spec
from PyInstaller.utils.hooks import collect_all

hiddenimports = ["fitz", "argostranslate.package", "argostranslate.translate"]
datas = []
binaries = []

for pkg in ["argostranslate", "PySide6"]:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h


a = Analysis(
    ["gui_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="pptx-translator-gui",
    console=False,
)
