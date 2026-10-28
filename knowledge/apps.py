from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "knowledge"
    verbose_name = "Knowledge base"

    def ready(self):
        from . import signals  # noqa: F401  (connects the signal handlers)
