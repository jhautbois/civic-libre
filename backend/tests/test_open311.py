"""Tests de contrat Open311 GeoReport v2, en JSON et en XML.

Le XML analysé ici est produit par notre propre application (contenu
de confiance), l'analyseur standard suffit.
"""

import xml.etree.ElementTree as ET

import pytest
from django.contrib.auth.models import User

from apps.reports import geocoding, services
from apps.reports.models import Category, Report


@pytest.fixture(autouse=True)
def _geocodage_hors_ligne(monkeypatch):
    monkeypatch.setattr(geocoding, "reverse", lambda lat, lon: "1 Place de la Mairie")
    monkeypatch.setattr(geocoding, "search", lambda q: None)


@pytest.fixture
def report(db):
    return services.create_report(
        category=Category.objects.get(code="voirie"),
        description="Trou dangereux devant la boulangerie",
        latitude=47.39,
        longitude=0.69,
        reporter_email="habitant@example.org",
    )


@pytest.mark.django_db
class TestDiscoveryEtServices:
    def test_discovery_xml(self, client):
        response = client.get("/open311/v2/discovery.xml")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/xml")
        root = ET.fromstring(response.content)
        assert root.tag == "discovery"
        assert root.find("endpoints/endpoint/specification").text.endswith("GeoReport_v2")

    def test_services_json_et_xml(self, client):
        data = client.get("/open311/v2/services.json").json()
        codes = {s["service_code"] for s in data}
        assert "voirie" in codes
        assert all(s["metadata"] == "false" and s["type"] == "realtime" for s in data)

        root = ET.fromstring(client.get("/open311/v2/services.xml").content)
        assert root.tag == "services"
        assert root.find("service/service_code") is not None

    def test_definition_service_inconnu_404(self, client):
        response = client.get("/open311/v2/services/inconnu.xml")
        assert response.status_code == 404
        assert ET.fromstring(response.content).tag == "errors"


@pytest.mark.django_db
class TestCreation:
    def test_post_formulaire_renvoie_service_request_id(self, client):
        response = client.post(
            "/open311/v2/requests.xml",
            {
                "service_code": "eclairage",
                "lat": "47.391",
                "long": "0.688",
                "description": "Lampadaire éteint depuis trois jours",
                "email": "habitant@example.org",
            },
        )
        assert response.status_code == 201
        root = ET.fromstring(response.content)
        request_id = root.find("request/service_request_id").text
        assert request_id.startswith("R-")
        report = Report.objects.get(reference=request_id)
        assert report.reporter_email == "habitant@example.org"

    def test_post_media_url_stockee_jamais_telechargee(self, client):
        response = client.post(
            "/open311/v2/requests.json",
            {
                "service_code": "voirie",
                "address_string": "12 rue des Écoles",
                "description": "Nid de poule",
                "media_url": "https://exemple.org/photo.jpg",
            },
        )
        assert response.status_code == 201
        report = Report.objects.latest("created_at")
        assert report.updates.get().media_url == "https://exemple.org/photo.jpg"
        assert not report.photos.exists()

    def test_post_sans_position_400(self, client):
        response = client.post(
            "/open311/v2/requests.xml",
            {"service_code": "voirie", "description": "sans position"},
        )
        assert response.status_code == 400
        assert ET.fromstring(response.content).find("error/description") is not None

    def test_post_service_inconnu_404(self, client):
        response = client.post(
            "/open311/v2/requests.json", {"service_code": "nimporte", "description": "x"}
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestLecture:
    def test_detail_minimise_avant_publication(self, client, report):
        data = client.get(f"/open311/v2/requests/{report.reference}.json").json()[0]
        assert data["service_request_id"] == report.reference
        assert data["status"] == "open"
        assert data["description"] == ""
        assert data["address"] == ""
        assert data["lat"] == ""
        assert data["status_notes"] == ""

    def test_liste_exclut_les_non_publies(self, client, report):
        assert client.get("/open311/v2/requests.json").json() == []
        report.publication_state = Report.Publication.PUBLISHED
        report.save()
        assert len(client.get("/open311/v2/requests.json").json()) == 1

    def test_detail_complet_apres_publication(self, client, report):
        report.publication_state = Report.Publication.PUBLISHED
        report.save()
        data = client.get(f"/open311/v2/requests/{report.reference}.json").json()[0]
        assert "boulangerie" in data["description"]
        assert data["address"] == "1 Place de la Mairie"
        assert data["lat"] == 47.39

    def test_courriel_jamais_expose(self, client, report):
        raw = client.get(f"/open311/v2/requests/{report.reference}.json").content.decode()
        assert "habitant@example.org" not in raw

    def test_liste_filtre_par_statut(self, client, report):
        report.publication_state = Report.Publication.PUBLISHED
        report.save()
        agent = User.objects.create_user("agent-x")
        services.transition_report(report=report, new_status="resolved", author=agent)
        assert client.get("/open311/v2/requests.json?status=open").json() == []
        closed = client.get("/open311/v2/requests.json?status=closed").json()
        assert closed[0]["status"] == "closed"

    def test_tokens_mode_temps_reel(self, client, report):
        data = client.get(f"/open311/v2/tokens/{report.reference}.json").json()[0]
        assert data["service_request_id"] == report.reference


@pytest.mark.django_db
class TestUpdatesFixMyStreet:
    def test_format_exact(self, client, report):
        report.publication_state = Report.Publication.PUBLISHED
        report.save()
        agent = User.objects.create_user("agent-y")
        services.transition_report(
            report=report,
            new_status="in_progress",
            public_comment="Intervention planifiée",
            author=agent,
        )
        response = client.get("/open311/v2/servicerequestupdates.xml")
        root = ET.fromstring(response.content)
        assert root.tag == "service_request_updates"
        update = root.find("request_update")
        assert update.find("update_id").text
        assert update.find("service_request_id").text == report.reference
        assert update.find("status").text == "IN_PROGRESS"
        assert update.find("updated_datetime").text  # ISO 8601 avec fuseau
        assert "+" in update.find("updated_datetime").text
        assert update.find("description").text == "Intervention planifiée"

    def test_statuts_etendus(self, client, report):
        report.publication_state = Report.Publication.PUBLISHED
        report.save()
        agent = User.objects.create_user("agent-z")
        services.transition_report(report=report, new_status="resolved", author=agent)
        data = client.get("/open311/v2/servicerequestupdates.json").json()
        assert data[-1]["status"] == "FIXED"

    def test_updates_exclut_les_non_publies_et_les_media(self, client, report):
        agent = User.objects.create_user("agent-w")
        services.transition_report(report=report, new_status="in_progress", author=agent)
        # Non publié : rien dans le flux public d'updates
        assert client.get("/open311/v2/servicerequestupdates.json").json() == []
        report.publication_state = Report.Publication.PUBLISHED
        report.save()
        data = client.get("/open311/v2/servicerequestupdates.json").json()
        assert len(data) == 1
        # media_url du déclarant jamais republiée sans modération
        assert data[0]["media_url"] == ""
