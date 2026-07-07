import datetime

import pytest
from django.utils import timezone

from apps.events import gancio, sync
from apps.events.models import MirroredEvent
from tests.fixtures_gancio import GANCIO_EVENTS


def _make_event(gancio_id=1, in_days=7, **kwargs):
    defaults = {
        "title": f"Événement {gancio_id}",
        "starts_at": timezone.now() + datetime.timedelta(days=in_days),
        "place_name": "Salle des fêtes",
    }
    defaults.update(kwargs)
    return MirroredEvent.objects.create(gancio_id=gancio_id, **defaults)


class TestParseGancio:
    def test_normalise_un_evenement_complet(self):
        parsed = gancio.parse_event(GANCIO_EVENTS[0])
        assert parsed["gancio_id"] == 42
        assert parsed["title"] == "Fête de la musique"
        assert parsed["starts_at"].tzinfo is not None
        assert parsed["place_name"] == "Place de la Mairie"
        assert parsed["tags"] == ["musique", "famille"]
        assert parsed["image_url"].endswith("/media/thumb/abcd1234.jpg")
        assert parsed["image_alt"] == "Affiche de la fête de la musique"
        assert parsed["source_url"].endswith("/event/fete-de-la-musique")

    def test_ignore_un_evenement_sans_titre(self):
        assert gancio.parse_event(GANCIO_EVENTS[2]) is None

    def test_parse_events_filtre_les_invalides(self):
        events = gancio.parse_events(GANCIO_EVENTS)
        assert [e["gancio_id"] for e in events] == [42, 43]


@pytest.mark.django_db
class TestSync:
    @pytest.fixture(autouse=True)
    def _description_detail(self, monkeypatch):
        """La liste Gancio n'inclut pas la description : appel détail simulé."""
        monkeypatch.setattr(
            gancio, "fetch_event_description", lambda slug: f"Description de {slug}"
        )

    def test_upsert_et_suppression(self, monkeypatch):
        monkeypatch.setattr(gancio, "fetch_raw_events", lambda: GANCIO_EVENTS)
        _make_event(gancio_id=999, title="Disparu en amont")

        sync.sync_gancio_events()

        ids = set(MirroredEvent.objects.values_list("gancio_id", flat=True))
        assert ids == {42, 43}
        fete = MirroredEvent.objects.get(gancio_id=42)
        assert fete.description == "Description de fete-de-la-musique"

    def test_la_mise_a_jour_preserve_notified(self, monkeypatch):
        """Une édition d'événement ne doit pas re-déclencher de notification."""
        monkeypatch.setattr(gancio, "fetch_raw_events", lambda: GANCIO_EVENTS)
        sync.sync_gancio_events()
        MirroredEvent.objects.filter(gancio_id=42).update(notified=True)

        sync.sync_gancio_events()

        assert MirroredEvent.objects.get(gancio_id=42).notified is True


@pytest.mark.django_db
class TestVues:
    def test_liste_affiche_les_evenements_a_venir(self, client):
        _make_event(gancio_id=1, title="Marché de Noël")
        _make_event(gancio_id=2, title="Événement passé", in_days=-3)

        response = client.get("/agenda/")
        html = response.content.decode()
        assert response.status_code == 200
        assert "Marché de Noël" in html
        assert "Événement passé" not in html

    def test_detail(self, client):
        _make_event(gancio_id=7, title="Réunion publique")
        response = client.get("/agenda/7/")
        assert response.status_code == 200
        assert "Réunion publique" in response.content.decode()

    def test_detail_inconnu_404(self, client):
        assert client.get("/agenda/12345/").status_code == 404

    def test_accueil_montre_les_prochains(self, client):
        _make_event(gancio_id=3, title="Loto des aînés")
        response = client.get("/")
        assert "Loto des aînés" in response.content.decode()


@pytest.mark.django_db
class TestFlux:
    def test_ics_conforme(self, client):
        event = _make_event(gancio_id=42, title="Fête de la musique")
        response = client.get("/flux/evenements.ics")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/calendar")

        from icalendar import Calendar

        cal = Calendar.from_ical(response.content)
        assert cal["METHOD"] == "PUBLISH"
        assert "NAME" in cal
        assert "REFRESH-INTERVAL" in cal
        assert "SOURCE" in cal

        entries = [c for c in cal.walk("VEVENT")]
        assert len(entries) == 1
        assert str(entries[0]["UID"]).startswith("evt-42@")
        assert str(entries[0]["SUMMARY"]) == "Fête de la musique"
        # TZID Europe/Paris exige le VTIMEZONE correspondant (RFC 5545).
        assert entries[0]["DTSTART"].params.get("TZID") == "Europe/Paris"
        timezones = [c for c in cal.walk("VTIMEZONE")]
        assert timezones, "VTIMEZONE manquant alors que TZID est utilisé"
        assert event.gancio_id == 42

    def test_rss_pointe_vers_la_pwa(self, client):
        _make_event(gancio_id=42, title="Fête de la musique")
        response = client.get("/flux/evenements.rss")
        assert response.status_code == 200

        import xml.dom.minidom

        doc = xml.dom.minidom.parseString(response.content)
        items = doc.getElementsByTagName("item")
        assert len(items) == 1
        link = items[0].getElementsByTagName("link")[0].firstChild.data
        assert "/agenda/42/" in link
        assert "gancio" not in link
        guid = items[0].getElementsByTagName("guid")[0].firstChild.data
        assert guid == link
        assert items[0].getElementsByTagName("pubDate")
