from django.contrib import admin

from .models import ChatLog, Escalation


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "channel", "language", "short_question", "escalated", "rating")
    list_filter = ("channel", "language", "escalated", "rating", "created_at")
    search_fields = ("question", "answer")
    date_hierarchy = "created_at"
    readonly_fields = [f.name for f in ChatLog._meta.fields]

    @admin.display(description="Question")
    def short_question(self, obj):
        return obj.question[:80]

    def has_add_permission(self, request):
        return False  # logs are written by the bot only


@admin.register(Escalation)
class EscalationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "status", "question", "contact", "handled_by")
    list_filter = ("status", "chat_log__channel")
    search_fields = ("chat_log__question", "contact", "staff_reply")
    readonly_fields = ("chat_log", "question", "contact", "handled_by", "created_at", "updated_at")
    fields = ("question", "contact", "status", "staff_reply", "handled_by", "chat_log", "created_at", "updated_at")

    @admin.display(description="Student question")
    def question(self, obj):
        return obj.chat_log.question

    def save_model(self, request, obj, form, change):
        obj.handled_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False  # created automatically when the bot can't answer
