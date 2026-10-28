"""Turn text into vectors for semantic search.

Backends (set EMBEDDING_BACKEND in .env):
- "e5":   intfloat/multilingual-e5-small, understands Khmer and English (384 dims)
- "hash": fast keyword-style vectors, no download; for tests and weak laptops
"""
from functools import lru_cache

from django.conf import settings

from .hash_embedding import DIM, hash_embed

EMBEDDING_DIM = DIM  # must match VectorField(dimensions=...) in models.py

# Default "how far is too far" cosine distance per backend.
# e5 scores most text as fairly similar, so its threshold is tight.
DEFAULT_MAX_DISTANCE = {"e5": 0.20, "hash": 0.70}


def backend() -> str:
    return settings.EMBEDDING_BACKEND


def max_distance() -> float:
    return settings.RAG_MAX_DISTANCE or DEFAULT_MAX_DISTANCE.get(backend(), 0.25)


@lru_cache(maxsize=1)
def _e5_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL)


def _e5_encode(texts: list[str]) -> list[list[float]]:
    vectors = _e5_model().encode(texts, normalize_embeddings=True, batch_size=32)
    return [v.tolist() for v in vectors]


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed knowledge-base text (FAQ entries, document chunks)."""
    if not texts:
        return []
    if backend() == "hash":
        return [hash_embed(t) for t in texts]
    # e5 models expect the "passage: " prefix for stored text
    return _e5_encode([f"passage: {t}" for t in texts])


def embed_query(text: str) -> list[float]:
    """Embed a student's question."""
    if backend() == "hash":
        return hash_embed(text)
    # ...and the "query: " prefix for questions
    return _e5_encode([f"query: {text}"])[0]
