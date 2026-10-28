"""A lightweight, dependency-free embedding for tests and weak laptops.

It is NOT semantic like the real e5 model: it only matches shared words and
character groups. Use EMBEDDING_BACKEND=e5 for real accuracy.
Pure Python (no Django import) so it can be unit-tested on its own.
"""
import hashlib
import math
import re

DIM = 384
_WORD = re.compile(r"\w+", re.UNICODE)


def _features(text: str) -> list[str]:
    text = text.lower()
    words = _WORD.findall(text)
    compact = re.sub(r"\s+", "", text)
    # Character trigrams help Khmer, which is written without spaces
    trigrams = [compact[i:i + 3] for i in range(max(len(compact) - 2, 0))]
    return [f"w:{w}" for w in words] + [f"c:{t}" for t in trigrams]


def hash_embed(text: str, dim: int = DIM) -> list[float]:
    vec = [0.0] * dim
    for feat in _features(text):
        digest = hashlib.md5(feat.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] & 1 else -1.0
        weight = 2.0 if feat.startswith("w:") else 1.0
        vec[index] += sign * weight
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        # Empty text: return a fixed unit vector so cosine distance stays defined
        vec[0] = 1.0
        return vec
    return [v / norm for v in vec]
