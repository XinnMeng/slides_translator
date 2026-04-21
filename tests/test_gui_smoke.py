from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from pptx_translator.gui.main_window import MainWindow


def test_main_window_starts() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert window.windowTitle() == "Document Translator Desktop"
    assert window.mode_combo.count() == 2
