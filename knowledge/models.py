from django.conf import settings
from django.db import models
from pgvector.django import HnswIndex, VectorField

from .services.embeddings import EMBEDDING_DIM


class Language(models.TextChoices):
    ENGLISH = "en", "English"
    KHMER = "km", "Khmer"


class Category(models.Model):
    """A topic such as Courses, Fees, Schedules, Services, Admissions."""

    name = models.CharField(max_length=100, unique=True)
    name_km = models.CharField("Name (Khmer)", max_length=100, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class FAQ(models.Model):
    """A question and its official answer, written by staff (US-10)."""

    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="faqs")
    question = models.CharField(max_length=500)
    answer = models.TextField()
    language = models.CharField(max_length=2, choices=Language.choices, default=Language.ENGLISH)
    is_active = models.BooleanField(default=True, help_text="Untick to hide this answer from the chatbot.")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__name", "question"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class Document(models.Model):
    """An uploaded official document such as a fee table or calendar (US-11)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="documents/", help_text="PDF, Word (.docx), .txt or .md")
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="documents"
    )
    language = models.CharField(max_length=2, choices=Language.choices, default=Language.ENGLISH)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(blank=True)
    chunk_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class Chunk(models.Model):
    """A searchable piece of knowledge with its embedding vector."""

    faq = models.ForeignKey(FAQ, null=True, blank=True, on_delete=models.CASCADE, related_name="chunks")
    document = models.ForeignKey(Document, null=True, blank=True, on_delete=models.CASCADE, related_name="chunks")
    source_title = models.CharField(max_length=300)
    text = models.TextField()
    language = models.CharField(max_length=2, choices=Language.choices, default=Language.ENGLISH)
    embedding = VectorField(dimensions=EMBEDDING_DIM)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            HnswIndex(
                name="chunk_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            )
        ]

    def __str__(self):
        return f"{self.source_title} ({len(self.text)} chars)"
