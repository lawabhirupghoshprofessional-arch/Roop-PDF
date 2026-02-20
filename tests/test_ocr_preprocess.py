from PIL import Image

from roop_pdfmd.core.models import AppSettings
from roop_pdfmd.core.ocr_preprocess import preprocess_for_ocr


def _make_gradient(width: int = 32, height: int = 8) -> Image.Image:
    image = Image.new("L", (width, height))
    for x in range(width):
        value = int((x / max(width - 1, 1)) * 255)
        for y in range(height):
            image.putpixel((x, y), value)
    return image.convert("RGB")


def test_preprocess_defaults_to_grayscale_with_autocontrast() -> None:
    img = Image.new("RGB", (10, 10), color=(120, 60, 20))
    settings = AppSettings()

    processed = preprocess_for_ocr(img, settings)

    assert processed.mode == "L"
    assert processed.size == (10, 10)


def test_preprocess_threshold_produces_binary_levels() -> None:
    img = _make_gradient()
    settings = AppSettings(
        ocr_preprocess_grayscale=True,
        ocr_preprocess_autocontrast=True,
        ocr_preprocess_threshold=True,
    )

    processed = preprocess_for_ocr(img, settings)
    values = set(processed.getdata())

    assert values.issubset({0, 255})
    assert 0 in values
    assert 255 in values


def test_preprocess_can_be_disabled() -> None:
    img = Image.new("RGB", (8, 8), color=(10, 20, 30))
    settings = AppSettings(
        ocr_preprocess_grayscale=False,
        ocr_preprocess_autocontrast=False,
        ocr_preprocess_threshold=False,
    )

    processed = preprocess_for_ocr(img, settings)

    assert processed.mode == "RGB"
