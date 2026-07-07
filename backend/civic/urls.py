from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.static import serve

from apps.announcements.feeds import AnnouncementsFeed
from apps.events.feeds import EventsFeed
from apps.events.ics import events_ics
from apps.ui import tiles

urlpatterns = [
    path("admin/", admin.site.urls),
    path("agenda/", include("apps.events.urls")),
    path("flux/evenements.ics", events_ics, name="events_ics"),
    path("flux/evenements.rss", EventsFeed(), name="events_rss"),
    path("flux/annonces.rss", AnnouncementsFeed(), name="announcements_rss"),
    path(
        "gestion/connexion/",
        auth_views.LoginView.as_view(),
        name="login",
    ),
    path("gestion/deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("apps.announcements.urls")),
    path("", include("apps.reports.urls")),
    path("tuiles/<int:z>/<int:x>/<int:y>.png", tiles.tile, name="tile"),
    # Images publiques des annonces (les photos de signalements passeront
    # par une vue contrôlée, jamais par ce chemin).
    path(
        "media/annonces/<path:path>",
        serve,
        {"document_root": settings.MEDIA_ROOT / "annonces"},
        name="announcement_media",
    ),
    path("", include("apps.ui.urls")),
]
