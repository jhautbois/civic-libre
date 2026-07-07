import pytest
from django.conf import settings


@pytest.mark.django_db
def test_accueil(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'lang="fr"' in html
    assert settings.CIVIC["COMMUNE_NAME"] in html
    assert "<main" in html
    assert "<h1>" in html


@pytest.mark.django_db
def test_sante(client):
    response = client.get("/sante")
    assert response.status_code == 200
    payload = response.json()
    assert payload["db"] == "ok"
    assert isinstance(payload["disk_free_mb"], int)
    assert "worker_heartbeat_age_s" in payload
