from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def get_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def get_resource_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            return Path(meipass).resolve()
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def get_resource_path(*parts: str) -> Path:
    return get_resource_base_dir().joinpath(*parts)


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    return ensure_dir(get_runtime_base_dir() / "logs")


def detect_tesseract_binary() -> str:
    env_path = os.environ.get("TESSERACT_PATH", "").strip()
    if _is_valid_binary_path(env_path):
        return str(Path(env_path).resolve())

    resolved = shutil.which("tesseract")
    if resolved and _is_valid_binary_path(resolved):
        return str(Path(resolved).resolve())

    for candidate in _platform_tesseract_candidates():
        if _is_valid_binary_path(candidate):
            return str(Path(candidate).resolve())

    return ""


def _platform_tesseract_candidates() -> list[Path]:
    if sys.platform.startswith("win"):
        env_candidates = [
            Path(os.environ.get("ProgramW6432", "")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("ProgramFiles", "")) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("ProgramFiles(x86)", ""))
            / "Tesseract-OCR"
            / "tesseract.exe",
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Programs"
            / "Tesseract-OCR"
            / "tesseract.exe",
            get_runtime_base_dir() / "tesseract" / "tesseract.exe",
        ]
        static_candidates = [
            Path(r"C:/Program Files/Tesseract-OCR/tesseract.exe"),
            Path(r"C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
        ]
        return env_candidates + static_candidates

    return [
        Path("/usr/bin/tesseract"),
        Path("/usr/local/bin/tesseract"),
        get_runtime_base_dir() / "tesseract" / "tesseract",
    ]


def _is_valid_binary_path(pathlike: str | Path) -> bool:
    if not pathlike:
        return False

    path = Path(pathlike)
    return path.exists() and path.is_file()
