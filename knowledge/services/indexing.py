"""Keep the search index (Chunk table) in sync with FAQs and documents."""
import logging

from django.db import transaction

from ..models import Chunk, Document, FAQ
from .chunking import split_text
from .embeddings import embed_passages
from .extraction import extract_text

logger = logging.getLogger(__name__)


def faq_text(faq: FAQ) -> str:
    return f"Q: {faq.question}\nA: {faq.answer}"


def index_faq(faq: FAQ) -> None:
    """Re-index one FAQ. Inactive FAQs are removed from search."""
    with transaction.atomic():
        faq.chunks.all().delete()
        if not faq.is_active:
            return
        text = faq_text(faq)
        Chunk.objects.create(
            faq=faq,
            source_title=faq.question[:300],
            text=text,
            language=faq.language,
            embedding=embed_passages([text])[0],
        )


def process_document(document: Document) -> None:
    """Extract, split and embed an uploaded document."""
    try:
        with document.file.open("rb") as fh:
            text = extract_text(fh, document.file.name)
        pieces = split_text(text)
        if not pieces:
            raise ValueError("No readable text found. Is this a scanned PDF? Upload a text-based file instead.")
        vectors = embed_passages(pieces)
        with transaction.atomic():
            document.chunks.all().delete()
            Chunk.objects.bulk_create(
                Chunk(
                    document=document,
                    source_title=document.title[:300],
                    text=piece,
                    language=document.language,
                    embedding=vector,
                )
                for piece, vector in zip(pieces, vectors)
            )
            # .update() avoids firing post_save again
            Document.objects.filter(pk=document.pk).update(
                status=Document.Status.READY, error="", chunk_count=len(pieces)
            )
    except Exception as exc:  # show the reason to staff in the admin
        logger.exception("Failed to process document %s", document.pk)
        Document.objects.filter(pk=document.pk).update(
            status=Document.Status.FAILED, error=str(exc)[:2000], chunk_count=0
        )
