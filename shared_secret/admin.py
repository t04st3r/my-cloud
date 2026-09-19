from django.contrib import admin

from .models import ShamirSS


@admin.display(description="Owner", ordering="owner__email")
def owner_display(obj):
    """Render the owner as 'First Last (email)', falling back to the username."""
    user = obj.owner
    return "%s (%s)" % (user.get_full_name() or user.username, user.email)


@admin.register(ShamirSS)
class ShamirSSAdmin(admin.ModelAdmin):
    list_display = ("name", "mers_exp", "k", "n", owner_display)
    list_select_related = ("owner",)
    search_fields = ("name", "owner__email", "owner__username")
