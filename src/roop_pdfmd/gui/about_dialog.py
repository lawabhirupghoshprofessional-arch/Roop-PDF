from __future__ import annotations

from PySide6.QtWidgets import QMessageBox, QWidget


def show_about_dialog(parent: QWidget) -> None:
    QMessageBox.about(
        parent,
        "About Roop PDF -> Markdown",
        "Roop PDF -> Markdown (English-only)\n\n"
        "Offline, no uploads.\n"
        "No telemetry by default.",
    )
