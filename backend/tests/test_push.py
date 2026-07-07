import datetime
import json

import pytest
from django.utils import timezone

from apps.announcements.models import Announcement
from apps.events.models import MirroredEvent
from apps.push import sender
from apps.push.models import NotificationDelivery, OutgoingNotification, PushSubscription


@pytest.fixture
def vapid_file(tmp_path, settings, monkeypatch):
    from django.core.management import call_command

    from apps.push import vapid

    vapid_path = tmp_path / "vapid.json"
    monkeypatch.setitem(settings.CIVIC, "VAPID_FILE", vapid_path)
    vapid.keys.cache_clear()
    call_command("ensure_vapid")
    yield vapid_path
    vapid.keys.cache_clear()


@pytest.fixture
def subscription(db):
    return PushSubscription.objects.create(
        endpoint="https://push.example/abc",
        p256dh="clef-p256dh",
        auth="clef-auth",
        topics=["events", "news", "alerts"],
    )


@pytest.mark.django_db
class TestApi:
    def test_cle_publique(self, client, vapid_file):
        data = client.get("/api/push/cle").json()
        assert data["cle_publique"]

    def test_abonnement_et_desabonnement(self, client):
        payload = {
            "endpoint": "https://push.example/xyz",
            "keys": {"p256dh": "p", "auth": "a"},
            "topics": ["alerts", "inconnu"],
        }
        response = client.post(
            "/api/push/abonnement", json.dumps(payload), content_type="application/json"
        )
        assert response.status_code == 200
        sub = PushSubscription.objects.get(endpoint="https://push.example/xyz")
        assert sub.topics == ["alerts"]

        response = client.post(
            "/api/push/desabonnement",
            json.dumps({"endpoint": "https://push.example/xyz"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert not PushSubscription.objects.exists()

    def test_abonnement_invalide_400(self, client):
        response = client.post(
            "/api/push/abonnement",
            json.dumps({"endpoint": "http://pas-https", "keys": {}}),
            content_type="application/json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestDetection:
    def test_annonce_notifie_une_seule_fois(self):
        annonce = Announcement.objects.create(
            title="Coupure du réseau", body="Mercredi matin.", level="alert"
        )
        sender.scan_announcements()
        sender.scan_announcements()
        assert OutgoingNotification.objects.count() == 1
        notification = OutgoingNotification.objects.get()
        assert notification.priority == "alert"
        assert notification.topic == "alerts"
        assert notification.title.startswith("Alerte :")
        annonce.refresh_from_db()
        assert annonce.notified is True

    def test_annonce_programmee_pas_encore_notifiee(self):
        Announcement.objects.create(
            title="Plus tard",
            body="x",
            published_at=timezone.now() + datetime.timedelta(days=1),
        )
        sender.scan_announcements()
        assert OutgoingNotification.objects.count() == 0

    def test_evenement_notifie_une_seule_fois(self):
        MirroredEvent.objects.create(
            gancio_id=1,
            title="Marché nocturne",
            starts_at=timezone.now() + datetime.timedelta(days=3),
        )
        sender.scan_events()
        sender.scan_events()
        assert OutgoingNotification.objects.count() == 1
        assert OutgoingNotification.objects.get().topic == "events"


@pytest.mark.django_db
class TestEnvoi:
    def test_envoi_reussi(self, monkeypatch, subscription, vapid_file):
        calls = []
        monkeypatch.setattr(sender, "webpush", lambda **kw: calls.append(kw))
        OutgoingNotification.objects.create(topic="news", title="Info", url="/annonces/1/")

        sender.send_pending()

        assert len(calls) == 1
        assert calls[0]["subscription_info"]["endpoint"] == subscription.endpoint
        assert calls[0]["ttl"] == 86400
        notification = OutgoingNotification.objects.get()
        assert notification.state == "done"
        delivery = NotificationDelivery.objects.get()
        assert delivery.state == "sent"
        subscription.refresh_from_db()
        assert subscription.last_success_at is not None

    def test_les_alertes_partent_en_premier(self, monkeypatch, subscription, vapid_file):
        order = []
        monkeypatch.setattr(
            sender, "webpush", lambda **kw: order.append(json.loads(kw["data"])["title"])
        )
        OutgoingNotification.objects.create(topic="news", title="Info banale")
        OutgoingNotification.objects.create(
            topic="alerts", title="Alerte inondation", priority="alert"
        )

        sender.send_pending()

        assert order[0] == "Alerte inondation"
        # TTL court et urgence haute pour les alertes
        assert order == ["Alerte inondation", "Info banale"]

    def test_abonnement_disparu_purge(self, monkeypatch, subscription, vapid_file):
        from pywebpush import WebPushException

        class FakeResponse:
            status_code = 410

        def gone(**kwargs):
            raise WebPushException("Gone", response=FakeResponse())

        monkeypatch.setattr(sender, "webpush", gone)
        OutgoingNotification.objects.create(topic="news", title="Info")

        sender.send_pending()

        assert not PushSubscription.objects.exists()
        assert OutgoingNotification.objects.get().state == "done"

    def test_pas_de_doublon_apres_reprise(self, monkeypatch, subscription, vapid_file):
        calls = []
        monkeypatch.setattr(sender, "webpush", lambda **kw: calls.append(1))
        notification = OutgoingNotification.objects.create(topic="news", title="Info")
        sender.send_pending()
        # Simule un état d'envoi interrompu re-signalé
        notification.refresh_from_db()
        notification.state = "pending"
        notification.save()
        sender.send_pending()
        assert len(calls) == 1, "une livraison déjà faite ne doit jamais être rejouée"


@pytest.mark.django_db
class TestPwa:
    def test_service_worker(self, client):
        response = client.get("/sw.js")
        assert response.status_code == 200
        assert "javascript" in response["Content-Type"]
        assert "push" in response.content.decode()

    def test_manifest(self, client):
        data = client.get("/manifest.webmanifest").json()
        assert data["display"] == "standalone"
        assert data["lang"] == "fr"
        assert len(data["icons"]) == 2

    def test_icone(self, client):
        response = client.get("/icone-192.png")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/png"

    def test_page_reglages(self, client):
        html = client.get("/notifications/").content.decode()
        assert "Activer les notifications" in html
        assert "écran d'accueil" in html or "écran d&#x27;accueil" in html
