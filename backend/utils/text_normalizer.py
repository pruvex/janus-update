from __future__ import annotations

import re
import unicodedata

_whitespace_re = re.compile(r"\s+", re.UNICODE)


def normalize_text(value: str) -> str:
    """Normalize user-provided text for prompt analysis.

    - Apply Unicode NFKC normalization
    - Trim and collapse whitespace
    - Ensure a lowercase baseline for comparisons
    """

    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = text.strip()
    text = _whitespace_re.sub(" ", text)
    return text.lower()
