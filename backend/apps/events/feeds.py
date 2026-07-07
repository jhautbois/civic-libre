"""Flux RSS des événements, généré par le cœur (docs/adr/0002).

Les liens et guid pointent vers la PWA, pas vers Gancio. Le pubDate
est la date de première synchronisation : une édition d'événement ne
re-notifie pas les lecteurs.
"""

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from .models import MirroredEvent


class EventsFeed(Feed):
    def title(self):
        return f"{settings.CIVIC['COMMUNE_NAME']} : agenda"

    def link(self):
        return reverse("events:list")

    def description(self):
        return f"Les événements à venir à {settings.CIVIC['COMMUNE_NAME']}."

    def items(self):
        return MirroredEvent.objects.filter(starts_at__gte=timezone.now()).order_by("starts_at")[
            :50
        ]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        quand = date_format(timezone.localtime(item.starts_at), "l j F Y à H:i")
        morceaux = [quand.capitalize()]
        if item.place_name:
            morceaux.append(item.place_name)
        if item.description:
            from django.utils.html import strip_tags

            morceaux.append(strip_tags(item.description)[:500])
        return " – ".join(morceaux)

    def item_link(self, item):
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.first_seen_at
