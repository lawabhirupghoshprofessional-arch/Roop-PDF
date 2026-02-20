from __future__ import annotations

from PySide6.QtCore import QSettings

from roop_pdfmd.core.models import AppSettings


_ORG = "Roop"
_APP = "RoopPDFMD"


def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def load_app_settings() -> AppSettings:
    settings = QSettings(_ORG, _APP)

    ocr_dpi = int(settings.value("ocr_dpi", 300))
    tesseract_path = str(settings.value("tesseract_path", "") or "")
    dehyphenate = _as_bool(settings.value("dehyphenate", False), False)
    ocr_only_if_no_text_layer = _as_bool(
        settings.value("ocr_only_if_no_text_layer", True), True
    )
    ocr_preprocess_grayscale = _as_bool(
        settings.value("ocr_preprocess_grayscale", True), True
    )
    ocr_preprocess_autocontrast = _as_bool(
        settings.value("ocr_preprocess_autocontrast", True), True
    )
    ocr_preprocess_threshold = _as_bool(
        settings.value("ocr_preprocess_threshold", False), False
    )

    return AppSettings(
        ocr_dpi=ocr_dpi,
        tesseract_path=tesseract_path,
        dehyphenate=dehyphenate,
        ocr_only_if_no_text_layer=ocr_only_if_no_text_layer,
        ocr_preprocess_grayscale=ocr_preprocess_grayscale,
        ocr_preprocess_autocontrast=ocr_preprocess_autocontrast,
        ocr_preprocess_threshold=ocr_preprocess_threshold,
    )


def save_app_settings(app_settings: AppSettings) -> None:
    settings = QSettings(_ORG, _APP)
    settings.setValue("ocr_dpi", app_settings.ocr_dpi)
    settings.setValue("tesseract_path", app_settings.tesseract_path)
    settings.setValue("dehyphenate", app_settings.dehyphenate)
    settings.setValue(
        "ocr_only_if_no_text_layer", app_settings.ocr_only_if_no_text_layer
    )
    settings.setValue("ocr_preprocess_grayscale", app_settings.ocr_preprocess_grayscale)
    settings.setValue(
        "ocr_preprocess_autocontrast", app_settings.ocr_preprocess_autocontrast
    )
    settings.setValue("ocr_preprocess_threshold", app_settings.ocr_preprocess_threshold)
    settings.sync()
