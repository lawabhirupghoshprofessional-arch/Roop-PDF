from roop_pdfmd.core.text_utils import dehyphenate_text


def test_dehyphenate_text_joins_linebreak_hyphenation() -> None:
    source = "This is hyphen-\nated text."
    assert dehyphenate_text(source) == "This is hyphenated text."
