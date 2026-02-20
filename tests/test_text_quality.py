from roop_pdfmd.core.text_quality import build_text_quality, should_use_ocr, text_signature


def test_should_extract_for_structured_text_quality() -> None:
    quality = build_text_quality(
        raw_text="This page contains real paragraph text with meaningful words and sentences.",
        text_block_count=4,
        bbox_coverage=0.35,
        image_area_ratio=0.05,
    )
    assert should_use_ocr(quality) is False


def test_should_ocr_for_near_empty_text() -> None:
    quality = build_text_quality(
        raw_text="   \n\n",
        text_block_count=0,
        bbox_coverage=0.0,
        image_area_ratio=0.9,
    )
    assert should_use_ocr(quality) is True


def test_should_ocr_for_garbage_lone_char_pattern() -> None:
    quality = build_text_quality(
        raw_text="a b c d e f g h i j k l",
        text_block_count=1,
        bbox_coverage=0.1,
        image_area_ratio=0.0,
    )
    assert quality.looks_garbage is True
    assert should_use_ocr(quality) is True


def test_should_ocr_for_repeated_short_header_like_text_on_image_page() -> None:
    quality = build_text_quality(
        raw_text="Chapter 7",
        text_block_count=1,
        bbox_coverage=0.03,
        image_area_ratio=0.65,
    )
    assert should_use_ocr(quality, repeated_short_signature=True) is True


def test_text_signature_is_stable_and_normalized() -> None:
    left = text_signature(" Header:  Intro  2026! ")
    right = text_signature("header intro 2026")
    assert left == right
