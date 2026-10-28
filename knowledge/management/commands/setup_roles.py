"""Create the staff roles used by the admin panel (US-12).

Usage:  python manage.py setup_roles
Then in the admin, tick "Staff status" on a user and add them to a group.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

EDITOR_PERMISSIONS = {
    "knowledge": [
        "add_faq", "change_faq", "delete_faq", "view_faq",
        "add_document", "change_document", "delete_document", "view_document",
        "add_category", "change_category", "view_category",
    ],
    "chat": ["view_chatlog", "view_escalation", "change_escalation"],
}


class Command(BaseCommand):
    help = "Create the Admin and Editor staff groups with their permissions."

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        admin_perms = Permission.objects.filter(content_type__app_label__in=["knowledge", "chat", "auth"])
        admin_group.permissions.set(admin_perms)

        editor_group, _ = Group.objects.get_or_create(name="Editor")
        editor_perms = Permission.objects.none()
        for app_label, codenames in EDITOR_PERMISSIONS.items():
            editor_perms |= Permission.objects.filter(content_type__app_label=app_label, codename__in=codenames)
        editor_group.permissions.set(editor_perms)

        self.stdout.write(self.style.SUCCESS(
            f"Admin group: {admin_group.permissions.count()} permissions. "
            f"Editor group: {editor_group.permissions.count()} permissions."
        ))
