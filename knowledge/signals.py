"""Re-index automatically whenever staff save an FAQ or upload a document."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Document, FAQ
from .services.indexing import index_faq, process_document


@receiver(post_save, sender=FAQ)
def faq_saved(sender, instance, **kwargs):
    index_faq(instance)


@receiver(post_save, sender=Document)
def document_saved(sender, instance, **kwargs):
    # Runs on every save in v1; processing is quick for normal-sized documents.
    process_document(instance)
