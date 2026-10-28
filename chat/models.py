from django.conf import settings
from django.db import models


class ChatLog(models.Model):
    """Every question and answer, used for reports (US-14) and ratings (US-13)."""

    class Channel(models.TextChoices):
        WEB = "web", "Website"
        TELEGRAM = "telegram", "Telegram"

    class Rating(models.IntegerChoices):
        HELPFUL = 1, "Helpful"
        NOT_HELPFUL = -1, "Not helpful"

    session_id = models.CharField(max_length=64, db_index=True)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.WEB)
    question = models.TextField()
    answer = models.TextField()
    language = models.CharField(max_length=2, default="en")
    sources = models.JSONField(default=list, blank=True)
    escalated = models.BooleanField(default=False)
    rating = models.SmallIntegerField(null=True, blank=True, choices=Rating.choices)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "chat log"

    def __str__(self):
        return self.question[:80]


class Escalation(models.Model):
    """A question the bot could not answer, handed to staff (US-08)."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ANSWERED = "answered", "Answered"
        CLOSED = "closed", "Closed"

    chat_log = models.OneToOneField(ChatLog, on_delete=models.CASCADE, related_name="escalation")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    contact = models.CharField(max_length=200, blank=True, help_text="How to reach the student, e.g. telegram:<chat id>")
    staff_reply = models.TextField(blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.chat_log.question[:60]}"
