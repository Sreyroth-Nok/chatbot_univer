"""The question-answering pipeline (RAG = Retrieval-Augmented Generation).

1. Detect the language   2. Find the most relevant knowledge chunks
3. Ask the AI to answer from those chunks only   4. Hand off to staff if unsure
5. Save the conversation for reports and ratings
"""
from dataclasses import asdict, dataclass, field

from django.conf import settings
from pgvector.django import CosineDistance

from knowledge.models import Chunk
from knowledge.services.embeddings import embed_query, max_distance

from ..models import ChatLog, Escalation
from .language import detect_language
from .llm import NOT_FOUND, generate_answer
from .messages import ESCALATED

MAX_QUESTION_CHARS = 1000


@dataclass
class ChatResult:
    answer: str
    language: str
    escalated: bool
    log_id: int
    sources: list = field(default_factory=list)

    def as_dict(self):
        return asdict(self)


def retrieve(question: str, top_k: int | None = None):
    """Return the most relevant chunks that are close enough to the question."""
    query_vector = embed_query(question)
    return list(
        Chunk.objects.select_related("faq", "document")
        .annotate(distance=CosineDistance("embedding", query_vector))
        .filter(distance__lte=max_distance())
        .order_by("distance")[: top_k or settings.RAG_TOP_K]
    )


def _direct_answer(chunk) -> str:
    """Fallback when the AI model is off: return the best FAQ answer as-is."""
    if chunk.faq_id:
        return chunk.faq.answer
    return chunk.text[:600]


def _sources(chunks) -> list[dict]:
    seen, result = set(), []
    for chunk in chunks:
        if chunk.source_title in seen:
            continue
        seen.add(chunk.source_title)
        result.append({"title": chunk.source_title, "type": "faq" if chunk.faq_id else "document"})
    return result


def answer_question(question: str, *, channel: str = ChatLog.Channel.WEB,
                    session_id: str = "", contact: str = "") -> ChatResult:
    question = question.strip()[:MAX_QUESTION_CHARS]
    language = detect_language(question)
    chunks = retrieve(question)

    answer, escalated = None, False
    if chunks:
        generated = generate_answer(question, chunks, language)
        if generated is None:
            answer = _direct_answer(chunks[0])
        elif generated.startswith(NOT_FOUND):
            escalated = True
        else:
            answer = generated
    else:
        escalated = True

    sources = [] if escalated else _sources(chunks)
    if escalated:
        answer = ESCALATED[language]

    log = ChatLog.objects.create(
        session_id=session_id[:64],
        channel=channel,
        question=question,
        answer=answer,
        language=language,
        sources=sources,
        escalated=escalated,
    )
    if escalated:
        Escalation.objects.create(chat_log=log, contact=contact[:200])

    return ChatResult(answer=answer, language=language, escalated=escalated, log_id=log.pk, sources=sources)


def save_rating(log_id: int, rating: int, session_id: str) -> bool:
    """Save a thumbs up/down. Only the session that asked can rate (US-13)."""
    updated = ChatLog.objects.filter(pk=log_id, session_id=session_id).update(rating=rating)
    return bool(updated)
