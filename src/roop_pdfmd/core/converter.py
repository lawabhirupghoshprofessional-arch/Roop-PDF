from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from threading import Event
from typing import Callable

import fitz
import pytesseract
from PIL import Image

from roop_pdfmd.core.models import (
    AppSettings,
    ConversionResult,
    PageMode,
    PageResult,
    ProgressEvent,
)
from roop_pdfmd.core.ocr_preprocess import preprocess_for_ocr
from roop_pdfmd.core.text_quality import detect_page_text_quality, should_use_ocr, text_signature
from roop_pdfmd.core.text_utils import dehyphenate_text
from roop_pdfmd.utils.logging_utils import get_logger
from roop_pdfmd.utils.paths import detect_tesseract_binary


ProgressCallback = Callable[[ProgressEvent], None]
PageCallback = Callable[[PageResult, str, str], None]


class ConversionError(Exception):
    """Raised when conversion cannot proceed."""


class Converter:
    def __init__(self, prescan_pages: int = 3) -> None:
        self._cancel_event = Event()
        self._logger = get_logger("converter")
        self._tesseract_ready = False
        self._prescan_pages = max(prescan_pages, 1)

    def cancel(self) -> None:
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def convert(
        self,
        input_pdf: str | Path,
        output_dir: str | Path,
        settings: AppSettings,
        progress_callback: ProgressCallback | None = None,
        page_callback: PageCallback | None = None,
    ) -> ConversionResult:
        self._cancel_event.clear()
        self._tesseract_ready = False

        input_pdf = Path(input_pdf).expanduser().resolve()
        output_dir = Path(output_dir).expanduser().resolve()

        if not input_pdf.exists() or not input_pdf.is_file():
            raise ConversionError(f"Input PDF not found: {input_pdf}")

        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / f"{input_pdf.stem}.md"
        text_path = output_dir / f"{input_pdf.stem}.txt"
        metadata_path = output_dir / f"{input_pdf.stem}.meta.json"

        start_time = time.perf_counter()
        page_results: list[PageResult] = []
        errors: list[str] = []
        md_blocks: list[str] = []
        txt_blocks: list[str] = []

        try:
            doc = fitz.open(input_pdf)
        except Exception as exc:  # pragma: no cover - backend-specific
            raise ConversionError(f"Unable to open PDF: {exc}") from exc

        total_pages = doc.page_count
        if total_pages <= 0:
            doc.close()
            raise ConversionError("PDF contains zero pages.")

        self._logger.info("Starting conversion | input=%s pages=%s", input_pdf, total_pages)

        if self._is_ocr_likely_needed(doc, settings):
            self._prepare_tesseract(settings)

        extracted_pages = 0
        ocr_pages = 0
        processed_pages = 0
        signature_counts: dict[str, int] = {}

        for idx in range(total_pages):
            page_number = idx + 1
            if self.is_cancelled():
                self._logger.info("Cancellation requested at page %s", page_number)
                break

            page = doc.load_page(idx)
            page_start = time.perf_counter()
            mode = PageMode.EXTRACT
            error_msg = ""
            text = ""

            try:
                extracted_text = page.get_text("text") or ""
                quality = detect_page_text_quality(page)
                page_sig = text_signature(extracted_text)
                repeated_short = bool(
                    page_sig
                    and quality.non_whitespace_len < 120
                    and signature_counts.get(page_sig, 0) >= 1
                )
                if page_sig:
                    signature_counts[page_sig] = signature_counts.get(page_sig, 0) + 1

                should_ocr_page = (
                    not settings.ocr_only_if_no_text_layer
                    or should_use_ocr(quality, repeated_short_signature=repeated_short)
                )

                if should_ocr_page:
                    mode = PageMode.OCR
                    text = self._ocr_page(page, settings)
                    ocr_pages += 1
                else:
                    mode = PageMode.EXTRACT
                    text = extracted_text
                    extracted_pages += 1

                if settings.dehyphenate:
                    text = dehyphenate_text(text)
            except Exception as exc:  # pragma: no cover - error path
                error_msg = str(exc)
                errors.append(f"Page {page_number}: {error_msg}")
                self._logger.exception("Page %s failed", page_number)

            block = self._format_page_block(page_number, text)
            md_blocks.append(block)
            txt_blocks.append(block)

            duration = time.perf_counter() - page_start
            page_result = PageResult(
                page_number=page_number,
                mode=mode,
                duration_seconds=duration,
                text_length=len(text),
                error=error_msg,
            )
            page_results.append(page_result)
            processed_pages += 1

            elapsed = time.perf_counter() - start_time
            eta = (elapsed / page_number) * max(total_pages - page_number, 0)
            progress = ProgressEvent(
                current_page=page_number,
                total_pages=total_pages,
                mode=mode,
                elapsed_seconds=elapsed,
                eta_seconds=eta,
            )

            if page_callback:
                page_callback(page_result, block, block)
            if progress_callback:
                progress_callback(progress)

        doc.close()

        markdown_content = "\n".join(md_blocks).strip() + "\n"
        text_content = "\n".join(txt_blocks).strip() + "\n"
        markdown_path.write_text(markdown_content, encoding="utf-8")
        text_path.write_text(text_content, encoding="utf-8")

        duration_seconds = time.perf_counter() - start_time
        cancelled = self.is_cancelled()
        result = ConversionResult(
            input_pdf=input_pdf,
            output_dir=output_dir,
            markdown_path=markdown_path,
            text_path=text_path,
            metadata_path=metadata_path,
            total_pages=total_pages,
            processed_pages=processed_pages,
            extracted_pages=extracted_pages,
            ocr_pages=ocr_pages,
            cancelled=cancelled,
            duration_seconds=duration_seconds,
            errors=errors,
            pages=page_results,
        )

        self._write_metadata(result)
        self._logger.info(
            "Conversion completed | processed=%s cancelled=%s errors=%s",
            processed_pages,
            cancelled,
            len(errors),
        )
        return result

    def _write_metadata(self, result: ConversionResult) -> None:
        payload = {
            "input_pdf": str(result.input_pdf),
            "output_dir": str(result.output_dir),
            "markdown_path": str(result.markdown_path),
            "text_path": str(result.text_path),
            "total_pages": result.total_pages,
            "processed_pages": result.processed_pages,
            "extracted_pages": result.extracted_pages,
            "ocr_pages": result.ocr_pages,
            "cancelled": result.cancelled,
            "duration_seconds": result.duration_seconds,
            "errors": result.errors,
            "pages": [
                {
                    **asdict(page),
                    "mode": page.mode.value,
                }
                for page in result.pages
            ],
        }
        result.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _is_ocr_likely_needed(self, doc: fitz.Document, settings: AppSettings) -> bool:
        if not settings.ocr_only_if_no_text_layer:
            return True

        signature_counts: dict[str, int] = {}
        scan_pages = min(doc.page_count, self._prescan_pages)

        for idx in range(scan_pages):
            page = doc.load_page(idx)
            quality = detect_page_text_quality(page)
            extracted_text = page.get_text("text") or ""
            page_sig = text_signature(extracted_text)

            repeated_short = bool(
                page_sig
                and quality.non_whitespace_len < 120
                and signature_counts.get(page_sig, 0) >= 1
            )
            if page_sig:
                signature_counts[page_sig] = signature_counts.get(page_sig, 0) + 1

            if should_use_ocr(quality, repeated_short_signature=repeated_short):
                self._logger.info("OCR likely needed based on pre-scan page %s", idx + 1)
                return True

        self._logger.info("OCR not needed for pre-scan pages")
        return False

    def _prepare_tesseract(self, settings: AppSettings) -> None:
        if self._tesseract_ready:
            return

        tesseract_cmd = settings.tesseract_path.strip() or detect_tesseract_binary()
        if not tesseract_cmd:
            raise ConversionError(
                "Tesseract OCR is required for this document, but no Tesseract binary was found. "
                "Install Tesseract (with English data) or set the binary path in Settings."
            )

        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        try:
            _ = pytesseract.get_tesseract_version()
        except Exception as exc:
            raise ConversionError(
                "Tesseract was found but could not be executed. "
                "Check the configured path in Settings and ensure the process has execute permissions."
            ) from exc

        self._logger.info("Using Tesseract command: %s", tesseract_cmd)
        self._tesseract_ready = True

    def _ocr_page(self, page: fitz.Page, settings: AppSettings) -> str:
        self._prepare_tesseract(settings)

        dpi = max(72, settings.ocr_dpi)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        mode = self._pixmap_mode(pix.n)
        image = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
        image = preprocess_for_ocr(image, settings)

        text = pytesseract.image_to_string(image, lang="eng")
        return text or ""

    @staticmethod
    def _pixmap_mode(channels: int) -> str:
        if channels == 1:
            return "L"
        if channels == 4:
            return "RGBA"
        return "RGB"

    @staticmethod
    def _format_page_block(page_number: int, text: str) -> str:
        normalized = text.rstrip("\n")
        if normalized:
            return f"--- Page {page_number} ---\n{normalized}\n"
        return f"--- Page {page_number} ---\n"
