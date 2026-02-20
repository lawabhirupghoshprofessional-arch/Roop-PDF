from __future__ import annotations

import re


_HYPHEN_BREAK_RE = re.compile(r"(\w)-\n(\w)")


def dehyphenate_text(text: str) -> str:
    """Join simple line-break hyphenations while preserving other text structure."""
    return _HYPHEN_BREAK_RE.sub(r"\1\2", text)
