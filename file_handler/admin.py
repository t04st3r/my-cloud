from django.contrib import admin

from .models import Document, Folder


@admin.display(description="Owner", ordering="owner__email")
def owner_display(obj):
    """Render the owner as 'First Last (email)', falling back to the username."""
    user = obj.owner
    return "%s (%s)" % (user.get_full_name() or user.username, user.email)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "folder", "scheme", owner_display, "creation_date")
    list_select_related = ("owner", "folder", "scheme")
    search_fields = ("name", "owner__email", "owner__username")


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", owner_display, "creation_date")
    list_select_related = ("owner", "parent")
    search_fields = ("name", "owner__email", "owner__username")
