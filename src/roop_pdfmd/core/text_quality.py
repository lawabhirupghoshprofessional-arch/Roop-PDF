from __future__ import annotations

import re
import unicodedata

import fitz

from roop_pdfmd.core.models import TextQuality


_TOKEN_RE = re.compile(r"[A-Za-z0-9']+")
_WHITESPACE_RE = re.compile(r"\s+")


def build_text_quality(
    raw_text: str,
    text_block_count: int,
    bbox_coverage: float,
    image_area_ratio: float,
) -> TextQuality:
    sanitized_text = raw_text or ""
    raw_text_len = len(sanitized_text)
    non_whitespace_text = _WHITESPACE_RE.sub("", sanitized_text)
    non_whitespace_len = len(non_whitespace_text)

    alpha_count = sum(1 for ch in non_whitespace_text if ch.isalpha())
    alpha_ratio = alpha_count / max(non_whitespace_len, 1)

    tokens = _TOKEN_RE.findall(sanitized_text.lower())
    unique_token_count = len(set(tokens))

    control_chars = sum(
        1
        for ch in sanitized_text
        if unicodedata.category(ch).startswith("C") and ch not in "\n\r\t"
    )
    control_char_ratio = control_chars / max(raw_text_len, 1)

    wordish_tokens = [tok for tok in re.findall(r"\S+", sanitized_text) if tok.strip()]
    lone_char_tokens = sum(1 for tok in wordish_tokens if _is_lone_char_token(tok))
    lone_char_token_ratio = lone_char_tokens / max(len(wordish_tokens), 1)

    looks_garbage = (
        control_char_ratio > 0.02
        or (lone_char_token_ratio > 0.8 and non_whitespace_len >= 10)
        or (lone_char_token_ratio > 0.55 and unique_token_count < 8)
        or (non_whitespace_len >= 20 and alpha_ratio < 0.12)
    )

    return TextQuality(
        raw_text_len=raw_text_len,
        non_whitespace_len=non_whitespace_len,
        alpha_ratio=alpha_ratio,
        unique_token_count=unique_token_count,
        text_block_count=max(text_block_count, 0),
        bbox_coverage=max(0.0, min(bbox_coverage, 1.0)),
        image_area_ratio=max(0.0, min(image_area_ratio, 1.0)),
        control_char_ratio=control_char_ratio,
        lone_char_token_ratio=lone_char_token_ratio,
        looks_garbage=looks_garbage,
    )


def detect_page_text_quality(page: fitz.Page) -> TextQuality:
    raw_text = page.get_text("text") or ""
    text_block_count, bbox_coverage = _text_block_stats(page)
    image_area_ratio = _image_area_ratio(page)
    return build_text_quality(raw_text, text_block_count, bbox_coverage, image_area_ratio)


def should_use_ocr(
    quality: TextQuality,
    repeated_short_signature: bool = False,
) -> bool:
    if quality.non_whitespace_len <= 10:
        return True
    if quality.looks_garbage:
        return True

    has_structured_text = (
        quality.text_block_count > 0
        and quality.non_whitespace_len >= 18
        and quality.alpha_ratio >= 0.2
        and quality.unique_token_count >= 3
    )

    if quality.non_whitespace_len < 35 and quality.image_area_ratio >= 0.35:
        return True

    if repeated_short_signature and quality.non_whitespace_len < 80 and quality.image_area_ratio >= 0.2:
        return True

    return not has_structured_text


def text_signature(raw_text: str) -> str:
    tokens = _TOKEN_RE.findall((raw_text or "").lower())
    if not tokens:
        return ""
    return " ".join(tokens[:20])


def _text_block_stats(page: fitz.Page) -> tuple[int, float]:
    blocks = page.get_text("blocks") or []
    if not blocks:
        return 0, 0.0

    page_area = max(float(page.rect.width * page.rect.height), 1.0)
    text_block_count = 0
    total_text_bbox_area = 0.0

    for block in blocks:
        if len(block) < 5:
            continue
        x0, y0, x1, y1, text = block[:5]
        if not str(text or "").strip():
            continue
        text_block_count += 1
        width = max(float(x1) - float(x0), 0.0)
        height = max(float(y1) - float(y0), 0.0)
        total_text_bbox_area += width * height

    return text_block_count, min(total_text_bbox_area / page_area, 1.0)


def _image_area_ratio(page: fitz.Page) -> float:
    page_area = max(float(page.rect.width * page.rect.height), 1.0)
    total_area = 0.0

    for image_info in page.get_images(full=True):
        if not image_info:
            continue
        xref = image_info[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            rects = []
        for rect in rects:
            total_area += max(float(rect.width * rect.height), 0.0)

    return min(total_area / page_area, 1.0)


def _is_lone_char_token(token: str) -> bool:
    trimmed = token.strip(".,;:!?\"'()[]{}")
    return len(trimmed) == 1 and trimmed.isalnum()
