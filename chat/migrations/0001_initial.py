import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.CharField(db_index=True, max_length=64)),
                (
                    "channel",
                    models.CharField(choices=[("web", "Website"), ("telegram", "Telegram")], default="web", max_length=10),
                ),
                ("question", models.TextField()),
                ("answer", models.TextField()),
                ("language", models.CharField(default="en", max_length=2)),
                ("sources", models.JSONField(blank=True, default=list)),
                ("escalated", models.BooleanField(default=False)),
                (
                    "rating",
                    models.SmallIntegerField(blank=True, choices=[(1, "Helpful"), (-1, "Not helpful")], null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"verbose_name": "chat log", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Escalation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Open"), ("answered", "Answered"), ("closed", "Closed")],
                        default="open", max_length=10,
                    ),
                ),
                (
                    "contact",
                    models.CharField(blank=True, help_text="How to reach the student, e.g. telegram:<chat id>", max_length=200),
                ),
                ("staff_reply", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "chat_log",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="escalation", to="chat.chatlog",
                    ),
                ),
                (
                    "handled_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
