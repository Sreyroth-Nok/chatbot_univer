"""Split long document text into overlapping chunks for search.

Pure Python (no Django import) so it can be unit-tested on its own.
"""
import re

MAX_CHARS = 800
OVERLAP_CHARS = 100


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    """Group paragraphs into chunks of at most ``max_chars``.

    A paragraph longer than ``max_chars`` is cut into windows that overlap by
    ``overlap`` characters, so a sentence cut in half still appears whole in
    one of the two chunks.
    """
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")
    text = normalize_whitespace(text)
    if not text:
        return []

    chunks: list[str] = []
    current = ""
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        if len(para) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            step = max_chars - overlap
            for start in range(0, len(para), step):
                piece = para[start:start + max_chars].strip()
                if piece:
                    chunks.append(piece)
                if start + max_chars >= len(para):
                    break
            continue
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks
