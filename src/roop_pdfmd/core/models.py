from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class PageMode(str, Enum):
    EXTRACT = "EXTRACT"
    OCR = "OCR"


@dataclass(slots=True)
class AppSettings:
    ocr_dpi: int = 300
    tesseract_path: str = ""
    dehyphenate: bool = False
    ocr_only_if_no_text_layer: bool = True
    ocr_preprocess_grayscale: bool = True
    ocr_preprocess_autocontrast: bool = True
    ocr_preprocess_threshold: bool = False


@dataclass(slots=True)
class TextQuality:
    raw_text_len: int
    non_whitespace_len: int
    alpha_ratio: float
    unique_token_count: int
    text_block_count: int
    bbox_coverage: float
    image_area_ratio: float
    control_char_ratio: float
    lone_char_token_ratio: float
    looks_garbage: bool


@dataclass(slots=True)
class ProgressEvent:
    current_page: int
    total_pages: int
    mode: PageMode
    elapsed_seconds: float
    eta_seconds: float


@dataclass(slots=True)
class PageResult:
    page_number: int
    mode: PageMode
    duration_seconds: float
    text_length: int
    error: str = ""


@dataclass(slots=True)
class ConversionResult:
    input_pdf: Path
    output_dir: Path
    markdown_path: Path
    text_path: Path
    metadata_path: Path
    total_pages: int
    processed_pages: int
    extracted_pages: int
    ocr_pages: int
    cancelled: bool
    duration_seconds: float
    errors: list[str] = field(default_factory=list)
    pages: list[PageResult] = field(default_factory=list)
