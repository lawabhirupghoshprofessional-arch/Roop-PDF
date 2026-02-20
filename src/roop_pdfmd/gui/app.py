from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from roop_pdfmd.gui.main_window import MainWindow
from roop_pdfmd.utils.logging_utils import setup_logging


def run_app(smoke: bool = False) -> int:
    setup_logging()

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()

    if smoke:
        QTimer.singleShot(150, app.quit)

    return app.exec()
