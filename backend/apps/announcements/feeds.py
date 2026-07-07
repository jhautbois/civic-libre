from django.conf import settings
from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import Announcement


class AnnouncementsFeed(Feed):
    def title(self):
        return f"{settings.CIVIC['COMMUNE_NAME']} : annonces"

    def link(self):
        return reverse("ui:home")

    def description(self):
        return f"Actualités et alertes de la mairie de {settings.CIVIC['COMMUNE_NAME']}."

    def items(self):
        return Announcement.objects.visible()[:50]

    def item_title(self, item):
        prefix = "[Alerte] " if item.level == Announcement.Level.ALERT else ""
        return f"{prefix}{item.title}"

    def item_description(self, item):
        return item.body[:1000]

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.published_at
