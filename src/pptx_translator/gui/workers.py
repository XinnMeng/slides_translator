from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal

from ..pipeline import run_translation
from ..pipelines.pdf_to_pptx_pipeline import run_pdf_to_pptx_translation
from ..translator import build_backend, check_argos_model_availability


@dataclass
class TranslationJobConfig:
    mode: str  # 'pptx' | 'pdf'
    input_path: Path
    output_path: Path
    source_lang: str
    target_lang: str
    backend: str
    argos_auto_install: bool
    argos_pivot_lang: str


class WorkerSignals(QObject):
    progress = Signal(int)
    log = Signal(str)
    error = Signal(str)
    finished = Signal(dict)


class TranslationWorker(QRunnable):
    def __init__(self, cfg: TranslationJobConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            self.signals.progress.emit(5)
            self.signals.log.emit("Preparing translator backend...")

            translator = build_backend(
                backend=self.cfg.backend,
                libretranslate_url="https://libretranslate.com/translate",
                libretranslate_api_key=None,
                argos_auto_install=self.cfg.argos_auto_install,
                argos_pivot_lang=self.cfg.argos_pivot_lang,
            )

            if self.cfg.backend in {"argos", "offline_argos"}:
                ok, msg = check_argos_model_availability(
                    source_lang=self.cfg.source_lang,
                    target_lang=self.cfg.target_lang,
                    pivot_lang=self.cfg.argos_pivot_lang,
                )
                self.signals.log.emit(msg)
                if not ok and not self.cfg.argos_auto_install:
                    raise RuntimeError(
                        msg + " Enable auto-install checkbox or install models manually."
                    )

            self.signals.progress.emit(20)
            self.signals.log.emit("Starting translation...")

            if self.cfg.mode == "pptx":
                result = run_translation(
                    input_path=self.cfg.input_path,
                    output_path=self.cfg.output_path,
                    source_lang=self.cfg.source_lang,
                    target_lang=self.cfg.target_lang,
                    translator=translator,
                    dry_run=False,
                )
            elif self.cfg.mode == "pdf":
                result = run_pdf_to_pptx_translation(
                    input_pdf=self.cfg.input_path,
                    output_pptx=self.cfg.output_path,
                    source_lang=self.cfg.source_lang,
                    target_lang=self.cfg.target_lang,
                    translator=translator,
                )
            else:
                raise RuntimeError(f"Unsupported mode: {self.cfg.mode}")

            self.signals.progress.emit(100)
            self.signals.log.emit("Translation completed.")
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))
