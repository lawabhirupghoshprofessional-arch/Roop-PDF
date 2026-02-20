from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from roop_pdfmd.core.models import AppSettings
from roop_pdfmd.utils.paths import detect_tesseract_binary


class SettingsDialog(QDialog):
    def __init__(self, current_settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)

        self.ocr_dpi_spin = QSpinBox(self)
        self.ocr_dpi_spin.setRange(72, 600)
        self.ocr_dpi_spin.setValue(current_settings.ocr_dpi)

        self.tesseract_path_input = QLineEdit(self)
        self.tesseract_path_input.setText(current_settings.tesseract_path)

        browse_button = QPushButton("Browse", self)
        browse_button.clicked.connect(self._browse_tesseract)

        autodetect_button = QPushButton("Auto-detect", self)
        autodetect_button.clicked.connect(self._autodetect_tesseract)

        path_row = QHBoxLayout()
        path_row.addWidget(self.tesseract_path_input)
        path_row.addWidget(browse_button)
        path_row.addWidget(autodetect_button)

        self.dehyphenate_checkbox = QCheckBox("De-hyphenate line-breaks", self)
        self.dehyphenate_checkbox.setChecked(current_settings.dehyphenate)

        self.ocr_only_checkbox = QCheckBox("OCR only if no text layer", self)
        self.ocr_only_checkbox.setChecked(current_settings.ocr_only_if_no_text_layer)

        self.ocr_preprocess_grayscale_checkbox = QCheckBox(
            "OCR preprocess: grayscale",
            self,
        )
        self.ocr_preprocess_grayscale_checkbox.setChecked(
            current_settings.ocr_preprocess_grayscale
        )

        self.ocr_preprocess_autocontrast_checkbox = QCheckBox(
            "OCR preprocess: autocontrast",
            self,
        )
        self.ocr_preprocess_autocontrast_checkbox.setChecked(
            current_settings.ocr_preprocess_autocontrast
        )

        self.ocr_preprocess_threshold_checkbox = QCheckBox(
            "OCR preprocess: threshold",
            self,
        )
        self.ocr_preprocess_threshold_checkbox.setChecked(
            current_settings.ocr_preprocess_threshold
        )

        form_layout = QFormLayout()
        form_layout.addRow("OCR DPI", self.ocr_dpi_spin)
        form_layout.addRow("Tesseract path", path_row)
        form_layout.addRow("", self.dehyphenate_checkbox)
        form_layout.addRow("", self.ocr_only_checkbox)
        form_layout.addRow("", self.ocr_preprocess_grayscale_checkbox)
        form_layout.addRow("", self.ocr_preprocess_autocontrast_checkbox)
        form_layout.addRow("", self.ocr_preprocess_threshold_checkbox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout()
        root.addLayout(form_layout)
        root.addWidget(buttons)
        self.setLayout(root)

    def get_settings(self) -> AppSettings:
        return AppSettings(
            ocr_dpi=self.ocr_dpi_spin.value(),
            tesseract_path=self.tesseract_path_input.text().strip(),
            dehyphenate=self.dehyphenate_checkbox.isChecked(),
            ocr_only_if_no_text_layer=self.ocr_only_checkbox.isChecked(),
            ocr_preprocess_grayscale=self.ocr_preprocess_grayscale_checkbox.isChecked(),
            ocr_preprocess_autocontrast=self.ocr_preprocess_autocontrast_checkbox.isChecked(),
            ocr_preprocess_threshold=self.ocr_preprocess_threshold_checkbox.isChecked(),
        )

    def _browse_tesseract(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Tesseract binary")
        if file_path:
            self.tesseract_path_input.setText(file_path)

    def _autodetect_tesseract(self) -> None:
        path = detect_tesseract_binary()
        if path:
            self.tesseract_path_input.setText(path)
            return
        QMessageBox.warning(
            self,
            "Tesseract not found",
            "Could not auto-detect Tesseract. Install it or set the full path manually.",
        )
