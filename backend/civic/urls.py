from django.contrib import admin
from django.urls import include, path

from apps.events.feeds import EventsFeed
from apps.events.ics import events_ics

urlpatterns = [
    path("admin/", admin.site.urls),
    path("agenda/", include("apps.events.urls")),
    path("flux/evenements.ics", events_ics, name="events_ics"),
    path("flux/evenements.rss", EventsFeed(), name="events_rss"),
    path("", include("apps.ui.urls")),
]
