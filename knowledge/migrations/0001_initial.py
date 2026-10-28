import django.db.models.deletion
import pgvector.django
from django.conf import settings
from django.db import migrations, models
from pgvector.django import VectorExtension

LANGUAGE_CHOICES = [("en", "English"), ("km", "Khmer")]


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Turns on the pgvector extension in PostgreSQL (must come first)
        VectorExtension(),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("name_km", models.CharField(blank=True, max_length=100, verbose_name="Name (Khmer)")),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "categories"},
        ),
        migrations.CreateModel(
            name="FAQ",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question", models.CharField(max_length=500)),
                ("answer", models.TextField()),
                ("language", models.CharField(choices=LANGUAGE_CHOICES, default="en", max_length=2)),
                ("is_active", models.BooleanField(default=True, help_text="Untick to hide this answer from the chatbot.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="faqs", to="knowledge.category",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"verbose_name": "FAQ", "verbose_name_plural": "FAQs", "ordering": ["category__name", "question"]},
        ),
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("file", models.FileField(help_text="PDF, Word (.docx), .txt or .md", upload_to="documents/")),
                ("language", models.CharField(choices=LANGUAGE_CHOICES, default="en", max_length=2)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Processing"), ("ready", "Ready"), ("failed", "Failed")],
                        default="pending", max_length=10,
                    ),
                ),
                ("error", models.TextField(blank=True)),
                ("chunk_count", models.PositiveIntegerField(default=0)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="documents", to="knowledge.category",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.CreateModel(
            name="Chunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_title", models.CharField(max_length=300)),
                ("text", models.TextField()),
                ("language", models.CharField(choices=LANGUAGE_CHOICES, default="en", max_length=2)),
                ("embedding", pgvector.django.VectorField(dimensions=384)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "document",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks", to="knowledge.document",
                    ),
                ),
                (
                    "faq",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks", to="knowledge.faq",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="chunk",
            index=pgvector.django.HnswIndex(
                ef_construction=64, fields=["embedding"], m=16,
                name="chunk_embedding_hnsw", opclasses=["vector_cosine_ops"],
            ),
        ),
    ]
