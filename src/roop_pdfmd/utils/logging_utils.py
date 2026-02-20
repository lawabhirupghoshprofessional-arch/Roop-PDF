from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from roop_pdfmd.utils.paths import get_logs_dir


_LOGGER_NAME = "roop_pdfmd"


def setup_logging(level: int = logging.INFO) -> Path:
    logs_dir = get_logs_dir()
    log_file = logs_dir / "roop_pdfmd.log"

    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return log_file


def get_logger(name: str | None = None) -> logging.Logger:
    if name:
        return logging.getLogger(f"{_LOGGER_NAME}.{name}")
    return logging.getLogger(_LOGGER_NAME)
