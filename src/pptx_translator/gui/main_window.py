from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from .workers import TranslationJobConfig, TranslationWorker


LANG_OPTIONS = [
    "de",
    "en",
    "ja",
    "zh",
    "zh-CN",
    "fr",
    "es",
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Document Translator Desktop")
        self.resize(900, 650)

        self.thread_pool = QThreadPool.globalInstance()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        root.addWidget(self._build_file_group())
        root.addWidget(self._build_options_group())
        root.addWidget(self._build_actions_group())

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        root.addWidget(self.progress_bar)

        self.log_panel = QPlainTextEdit()
        self.log_panel.setReadOnly(True)
        root.addWidget(self.log_panel)

        self._on_mode_changed()

    def _build_file_group(self) -> QGroupBox:
        box = QGroupBox("Files")
        layout = QGridLayout(box)

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()

        input_btn = QPushButton("Browse Input...")
        output_btn = QPushButton("Browse Output...")
        input_btn.clicked.connect(self._browse_input)
        output_btn.clicked.connect(self._browse_output)

        layout.addWidget(QLabel("Input file:"), 0, 0)
        layout.addWidget(self.input_edit, 0, 1)
        layout.addWidget(input_btn, 0, 2)

        layout.addWidget(QLabel("Output file:"), 1, 0)
        layout.addWidget(self.output_edit, 1, 1)
        layout.addWidget(output_btn, 1, 2)

        return box

    def _build_options_group(self) -> QGroupBox:
        box = QGroupBox("Options")
        layout = QGridLayout(box)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["PPTX translate", "PDF to translated PPTX"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        self.source_combo.addItems(LANG_OPTIONS)
        self.target_combo.addItems(LANG_OPTIONS)

        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["offline_argos", "argos", "libretranslate"])
        self.backend_combo.setCurrentText("offline_argos")

        self.auto_install_cb = QCheckBox("Auto-install missing Argos models")
        self.auto_install_cb.setChecked(True)

        self.pivot_edit = QLineEdit("en")

        layout.addWidget(QLabel("Mode:"), 0, 0)
        layout.addWidget(self.mode_combo, 0, 1)

        layout.addWidget(QLabel("Source language:"), 1, 0)
        layout.addWidget(self.source_combo, 1, 1)

        layout.addWidget(QLabel("Target language:"), 2, 0)
        layout.addWidget(self.target_combo, 2, 1)

        layout.addWidget(QLabel("Backend:"), 3, 0)
        layout.addWidget(self.backend_combo, 3, 1)

        layout.addWidget(QLabel("Argos pivot language:"), 4, 0)
        layout.addWidget(self.pivot_edit, 4, 1)

        layout.addWidget(self.auto_install_cb, 5, 0, 1, 2)

        return box

    def _build_actions_group(self) -> QGroupBox:
        box = QGroupBox("Actions")
        layout = QHBoxLayout(box)

        self.translate_btn = QPushButton("Translate")
        self.translate_btn.clicked.connect(self._start_translation)

        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.log_panel.clear)

        layout.addWidget(self.translate_btn)
        layout.addWidget(clear_btn)
        return box

    def _on_mode_changed(self) -> None:
        mode = self.mode_combo.currentText()
        if mode == "PDF to translated PPTX":
            self.source_combo.setCurrentText("ja")
            self.target_combo.setCurrentText("zh-CN")
            self.backend_combo.setCurrentText("offline_argos")

    def _browse_input(self) -> None:
        mode = self.mode_combo.currentText()
        if mode == "PPTX translate":
            path, _ = QFileDialog.getOpenFileName(self, "Select input PPTX", "", "PowerPoint (*.pptx)")
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select input PDF", "", "PDF (*.pdf)")
        if path:
            self.input_edit.setText(path)

    def _browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Select output PPTX", "", "PowerPoint (*.pptx)")
        if path:
            if not path.lower().endswith(".pptx"):
                path += ".pptx"
            self.output_edit.setText(path)

    def _append_log(self, message: str) -> None:
        self.log_panel.appendPlainText(message)

    def _validate_inputs(self) -> str | None:
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()

        if not input_path:
            return "Please choose an input file."
        if not output_path:
            return "Please choose an output file."

        mode = self.mode_combo.currentText()
        if mode == "PPTX translate" and not input_path.lower().endswith(".pptx"):
            return "Input must be a .pptx file for PPTX mode."
        if mode == "PDF to translated PPTX" and not input_path.lower().endswith(".pdf"):
            return "Input must be a .pdf file for PDF mode."
        if not output_path.lower().endswith(".pptx"):
            return "Output must be a .pptx file."

        if not Path(input_path).exists():
            return "Input file does not exist."

        return None

    def _set_running(self, running: bool) -> None:
        self.translate_btn.setEnabled(not running)
        if running:
            self.progress_bar.setValue(0)

    def _start_translation(self) -> None:
        error = self._validate_inputs()
        if error:
            QMessageBox.critical(self, "Validation Error", error)
            return

        mode = "pptx" if self.mode_combo.currentText() == "PPTX translate" else "pdf"

        cfg = TranslationJobConfig(
            mode=mode,
            input_path=Path(self.input_edit.text().strip()),
            output_path=Path(self.output_edit.text().strip()),
            source_lang=self.source_combo.currentText(),
            target_lang=self.target_combo.currentText(),
            backend=self.backend_combo.currentText(),
            argos_auto_install=self.auto_install_cb.isChecked(),
            argos_pivot_lang=self.pivot_edit.text().strip() or "en",
        )

        self._set_running(True)
        self._append_log("Starting translation job...")

        worker = TranslationWorker(cfg)
        worker.signals.log.connect(self._append_log)
        worker.signals.progress.connect(self.progress_bar.setValue)
        worker.signals.error.connect(self._on_error)
        worker.signals.finished.connect(self._on_finished)
        self.thread_pool.start(worker)

    def _on_error(self, message: str) -> None:
        self._set_running(False)
        self.progress_bar.setValue(0)
        self._append_log(f"ERROR: {message}")
        QMessageBox.critical(self, "Translation Failed", message)

    def _on_finished(self, result: dict) -> None:
        self._set_running(False)
        self.progress_bar.setValue(100)
        output = result.get("output", "(unknown)")
        self._append_log(f"Success: output saved to {output}")
        QMessageBox.information(self, "Translation Complete", f"Output saved to:\n{output}")
