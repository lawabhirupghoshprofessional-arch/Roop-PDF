from __future__ import annotations

from PIL import Image, ImageOps

from roop_pdfmd.core.models import AppSettings


def preprocess_for_ocr(image: Image.Image, settings: AppSettings) -> Image.Image:
    processed = image.convert("RGB")

    if settings.ocr_preprocess_grayscale:
        processed = ImageOps.grayscale(processed)

    if settings.ocr_preprocess_autocontrast:
        processed = ImageOps.autocontrast(processed)

    if settings.ocr_preprocess_threshold:
        gray = processed if processed.mode == "L" else ImageOps.grayscale(processed)
        threshold = _otsu_threshold(gray)
        processed = gray.point(lambda value: 255 if value >= threshold else 0, mode="L")

    return processed


def _otsu_threshold(gray_image: Image.Image) -> int:
    histogram = gray_image.histogram()
    total = sum(histogram)
    if total <= 0:
        return 127

    sum_total = 0.0
    for i, count in enumerate(histogram[:256]):
        sum_total += i * count

    sum_background = 0.0
    weight_background = 0
    max_variance = -1.0
    threshold = 127

    for i, count in enumerate(histogram[:256]):
        weight_background += count
        if weight_background == 0:
            continue

        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break

        sum_background += i * count
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground

        variance = (
            float(weight_background)
            * float(weight_foreground)
            * (mean_background - mean_foreground) ** 2
        )

        if variance > max_variance:
            max_variance = variance
            threshold = i

    return threshold
