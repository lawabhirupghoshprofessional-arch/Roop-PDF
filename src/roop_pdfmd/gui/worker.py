from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from roop_pdfmd.core.converter import ConversionError, Converter
from roop_pdfmd.core.models import AppSettings, ConversionResult, PageResult, ProgressEvent


class ConversionWorker(QObject):
    progress = Signal(int, int, str, float, float)
    preview_chunk = Signal(str, str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        input_pdf: str,
        output_dir: str,
        settings: AppSettings,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._input_pdf = input_pdf
        self._output_dir = output_dir
        self._settings = settings
        self._converter = Converter()

    @Slot()
    def run(self) -> None:
        try:
            result = self._converter.convert(
                self._input_pdf,
                self._output_dir,
                self._settings,
                progress_callback=self._on_progress,
                page_callback=self._on_page,
            )
            self.finished.emit(result)
        except ConversionError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # pragma: no cover - defensive
            self.failed.emit(f"Unexpected error: {exc}")

    @Slot()
    def cancel(self) -> None:
        self._converter.cancel()

    def _on_progress(self, event: ProgressEvent) -> None:
        self.progress.emit(
            event.current_page,
            event.total_pages,
            event.mode.value,
            event.elapsed_seconds,
            event.eta_seconds,
        )

    def _on_page(self, _: PageResult, markdown_text: str, plain_text: str) -> None:
        self.preview_chunk.emit(markdown_text, plain_text)
