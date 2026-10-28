"""Detect whether a message is Khmer or English (US-05).

Pure Python (no Django import) so it can be unit-tested on its own.
Khmer script lives in Unicode blocks U+1780–U+17FF and U+19E0–U+19FF.
"""

KHMER = "km"
ENGLISH = "en"


def _is_khmer(ch: str) -> bool:
    code = ord(ch)
    return 0x1780 <= code <= 0x17FF or 0x19E0 <= code <= 0x19FF


def detect_language(text: str, threshold: float = 0.3) -> str:
    """Return "km" if at least ``threshold`` of the letters are Khmer, else "en"."""
    letters = [ch for ch in text if ch.isalpha() or _is_khmer(ch)]
    if not letters:
        return ENGLISH
    khmer = sum(1 for ch in letters if _is_khmer(ch))
    return KHMER if khmer / len(letters) >= threshold else ENGLISH
