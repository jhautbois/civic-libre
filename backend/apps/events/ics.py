"""Export iCal des événements, généré par le cœur (docs/adr/0002).

Conformité visée : RFC 5545 (UID stables, TZID Europe/Paris avec
VTIMEZONE) et RFC 7986 (NAME, SOURCE, REFRESH-INTERVAL). Fenêtre
glissante identique à celle du miroir.
"""

import datetime
import zoneinfo

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from icalendar import Calendar, Event, vDuration, vUri

from .models import MirroredEvent

PARIS = zoneinfo.ZoneInfo("Europe/Paris")


def events_ics(request):
    commune = settings.CIVIC["COMMUNE_NAME"]
    feed_url = request.build_absolute_uri()

    cal = Calendar()
    cal.add("prodid", "-//Civic Libre//FR")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("name", f"{commune} : agenda")
    cal.add("x-wr-calname", f"{commune} : agenda")
    cal.add("source", vUri(feed_url))
    cal.add("refresh-interval", vDuration(datetime.timedelta(days=1)))
    cal.add("x-published-ttl", "P1D")

    for event in MirroredEvent.objects.all():
        entry = Event()
        entry.add("uid", f"evt-{event.gancio_id}@{settings.CIVIC_DOMAIN}")
        entry.add("dtstamp", event.synced_at)
        entry.add("dtstart", event.starts_at.astimezone(PARIS))
        if event.ends_at:
            entry.add("dtend", event.ends_at.astimezone(PARIS))
        entry.add("summary", event.title)
        if event.description:
            from django.utils.html import strip_tags

            entry.add("description", strip_tags(event.description))
        location = ", ".join(p for p in [event.place_name, event.place_address] if p)
        if location:
            entry.add("location", location)
        entry.add("url", vUri(request.build_absolute_uri(event.get_absolute_url())))
        cal.add_component(entry)

    cal.add_missing_timezones()

    response = HttpResponse(cal.to_ical(), content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = 'inline; filename="evenements.ics"'
    response["Last-Modified"] = timezone.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
    return response
