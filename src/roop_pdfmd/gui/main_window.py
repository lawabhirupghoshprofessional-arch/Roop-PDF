from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QDesktopServices, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from roop_pdfmd.core.models import AppSettings, ConversionResult
from roop_pdfmd.gui.about_dialog import show_about_dialog
from roop_pdfmd.gui.settings_dialog import SettingsDialog
from roop_pdfmd.gui.settings_store import load_app_settings, save_app_settings
from roop_pdfmd.gui.worker import ConversionWorker
from roop_pdfmd.utils.logging_utils import get_logger
from roop_pdfmd.utils.paths import get_logs_dir


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._logger = get_logger("gui")
        self._thread: QThread | None = None
        self._worker: ConversionWorker | None = None
        self._last_result: ConversionResult | None = None
        self._settings: AppSettings = load_app_settings()

        self.setWindowTitle("Roop PDF -> Markdown (English-only)")
        self.resize(980, 700)

        self._build_ui()
        self.statusBar().showMessage("Ready")

    def _build_ui(self) -> None:
        root = QWidget(self)
        main_layout = QVBoxLayout(root)

        io_group = QGroupBox("Input / Output", root)
        io_layout = QGridLayout(io_group)

        self.pdf_input = QLineEdit(io_group)
        self.out_input = QLineEdit(io_group)

        pdf_button = QPushButton("Select PDF", io_group)
        pdf_button.clicked.connect(self._select_pdf)

        out_button = QPushButton("Select Output Folder", io_group)
        out_button.clicked.connect(self._select_output_dir)

        io_layout.addWidget(QLabel("PDF file"), 0, 0)
        io_layout.addWidget(self.pdf_input, 0, 1)
        io_layout.addWidget(pdf_button, 0, 2)
        io_layout.addWidget(QLabel("Output folder"), 1, 0)
        io_layout.addWidget(self.out_input, 1, 1)
        io_layout.addWidget(out_button, 1, 2)

        controls_row = QHBoxLayout()
        self.start_button = QPushButton("Start conversion", root)
        self.start_button.clicked.connect(self._start_conversion)

        self.cancel_button = QPushButton("Cancel", root)
        self.cancel_button.clicked.connect(self._cancel_conversion)
        self.cancel_button.setEnabled(False)

        self.open_output_button = QPushButton("Open output folder", root)
        self.open_output_button.clicked.connect(self._open_output_folder)
        self.open_output_button.setEnabled(False)

        self.settings_button = QPushButton("Settings", root)
        self.settings_button.clicked.connect(self._open_settings)

        self.view_logs_button = QPushButton("View logs", root)
        self.view_logs_button.clicked.connect(self._view_logs)

        self.about_button = QPushButton("About", root)
        self.about_button.clicked.connect(self._show_about)

        controls_row.addWidget(self.start_button)
        controls_row.addWidget(self.cancel_button)
        controls_row.addWidget(self.open_output_button)
        controls_row.addStretch(1)
        controls_row.addWidget(self.settings_button)
        controls_row.addWidget(self.view_logs_button)
        controls_row.addWidget(self.about_button)

        progress_group = QGroupBox("Progress", root)
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar(progress_group)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        summary = QFormLayout()
        self.page_value = QLabel("0 / 0", progress_group)
        self.mode_value = QLabel("-", progress_group)
        self.elapsed_value = QLabel("00:00", progress_group)
        self.eta_value = QLabel("--:--", progress_group)

        summary.addRow("Page", self.page_value)
        summary.addRow("Mode", self.mode_value)
        summary.addRow("Elapsed", self.elapsed_value)
        summary.addRow("ETA", self.eta_value)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(summary)

        self.preview_tabs = QTabWidget(root)
        self.markdown_preview = QPlainTextEdit(root)
        self.markdown_preview.setReadOnly(True)
        self.text_preview = QPlainTextEdit(root)
        self.text_preview.setReadOnly(True)
        self.preview_tabs.addTab(self.markdown_preview, "Markdown")
        self.preview_tabs.addTab(self.text_preview, "Text")

        main_layout.addWidget(io_group)
        main_layout.addLayout(controls_row)
        main_layout.addWidget(progress_group)
        main_layout.addWidget(self.preview_tabs)

        self.setCentralWidget(root)

    def _select_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", filter="PDF files (*.pdf)")
        if path:
            self.pdf_input.setText(path)

    def _select_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select output folder")
        if path:
            self.out_input.setText(path)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec():
            self._settings = dialog.get_settings()
            save_app_settings(self._settings)

    def _show_about(self) -> None:
        show_about_dialog(self)

    def _view_logs(self) -> None:
        logs_dir = get_logs_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_dir)))

    def _start_conversion(self) -> None:
        input_pdf = self.pdf_input.text().strip()
        output_dir = self.out_input.text().strip()

        if not input_pdf:
            QMessageBox.warning(self, "Missing input", "Select a PDF file first.")
            return
        if not output_dir:
            QMessageBox.warning(self, "Missing output", "Select an output folder first.")
            return
        if not Path(input_pdf).exists():
            QMessageBox.warning(self, "Invalid input", "Selected PDF does not exist.")
            return

        self._set_running_state(True)
        self._reset_progress()
        self._last_result = None

        self._thread = QThread(self)
        self._worker = ConversionWorker(input_pdf, output_dir, self._settings)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.preview_chunk.connect(self._on_preview_chunk)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)

        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()
        self.statusBar().showMessage("Conversion started")

    def _cancel_conversion(self) -> None:
        if self._worker:
            self._worker.cancel()
            self.statusBar().showMessage("Cancellation requested. Waiting for current page...")

    def _on_progress(
        self,
        current_page: int,
        total_pages: int,
        mode: str,
        elapsed_seconds: float,
        eta_seconds: float,
    ) -> None:
        self.progress_bar.setRange(0, max(total_pages, 1))
        self.progress_bar.setValue(current_page)
        self.page_value.setText(f"{current_page} / {total_pages}")
        self.mode_value.setText(mode)
        self.elapsed_value.setText(self._fmt_duration(elapsed_seconds))
        self.eta_value.setText(self._fmt_duration(eta_seconds))

    def _on_preview_chunk(self, markdown_chunk: str, plain_text_chunk: str) -> None:
        self._append_preview_text(self.markdown_preview, markdown_chunk)
        self._append_preview_text(self.text_preview, plain_text_chunk)

    def _on_finished(self, result: object) -> None:
        if not isinstance(result, ConversionResult):
            self._on_failed("Unexpected worker result.")
            return

        self._last_result = result
        self._set_running_state(False)
        self.open_output_button.setEnabled(True)

        message = (
            f"Conversion finished. Processed {result.processed_pages}/{result.total_pages} pages.\n"
            f"Markdown: {result.markdown_path}\n"
            f"Text: {result.text_path}\n"
            f"Metadata: {result.metadata_path}"
        )
        if result.cancelled:
            message = "Conversion cancelled.\n" + message
        if result.errors:
            message += f"\n\nEncountered {len(result.errors)} page-level error(s). Check logs."

        self.statusBar().showMessage("Conversion complete")
        QMessageBox.information(self, "Done", message)

    def _on_failed(self, error_message: str) -> None:
        self._logger.error("Conversion failed: %s", error_message)
        self._set_running_state(False)
        self.statusBar().showMessage("Conversion failed")

        if "Tesseract" in error_message:
            friendly = (
                "Tesseract OCR is required for pages that need OCR.\n\n"
                "Install Tesseract with English language data, then set the path in Settings if needed.\n\n"
                f"Details: {error_message}"
            )
            QMessageBox.warning(self, "Tesseract required", friendly)
            return

        QMessageBox.critical(self, "Conversion failed", error_message)

    def _set_running_state(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.settings_button.setEnabled(not running)

    def _open_output_folder(self) -> None:
        folder = None
        if self._last_result:
            folder = self._last_result.output_dir
        else:
            current = self.out_input.text().strip()
            if current:
                folder = Path(current)

        if folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _reset_progress(self) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.page_value.setText("0 / 0")
        self.mode_value.setText("-")
        self.elapsed_value.setText("00:00")
        self.eta_value.setText("--:--")
        self.markdown_preview.clear()
        self.text_preview.clear()

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        total_seconds = max(int(seconds), 0)
        minutes = total_seconds // 60
        secs = total_seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def _append_preview_text(widget: QPlainTextEdit, chunk: str) -> None:
        cursor = widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(chunk)
        widget.setTextCursor(cursor)
        widget.ensureCursorVisible()
