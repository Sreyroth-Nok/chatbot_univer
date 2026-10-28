from django.contrib import admin, messages

from .models import Category, Document, FAQ
from .services.indexing import index_faq, process_document


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "name_km")
    search_fields = ("name", "name_km")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "language", "is_active", "updated_at", "updated_by")
    list_filter = ("category", "language", "is_active")
    search_fields = ("question", "answer")
    readonly_fields = ("updated_by", "created_at", "updated_at")
    list_per_page = 50
    actions = ["reindex"]

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Re-index selected FAQs")
    def reindex(self, request, queryset):
        for faq in queryset:
            index_faq(faq)
        self.message_user(request, f"Re-indexed {queryset.count()} FAQ(s).", messages.SUCCESS)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "language", "status", "chunk_count", "uploaded_at", "uploaded_by")
    list_filter = ("status", "category", "language")
    search_fields = ("title",)
    readonly_fields = ("status", "error", "chunk_count", "uploaded_by", "uploaded_at")
    actions = ["reprocess"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Re-process selected documents")
    def reprocess(self, request, queryset):
        for doc in queryset:
            process_document(doc)
        self.message_user(request, f"Re-processed {queryset.count()} document(s).", messages.SUCCESS)
