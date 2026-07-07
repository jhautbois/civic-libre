from django.contrib import admin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "level", "is_pinned", "published_at", "expires_at"]
    list_filter = ["level", "is_pinned"]
    search_fields = ["title", "body"]
