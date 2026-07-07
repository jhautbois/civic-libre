import json

from django.conf import settings
from django.core.management import call_command


def test_ensure_vapid_cree_les_cles(tmp_path, monkeypatch):
    vapid_file = tmp_path / "vapid.json"
    monkeypatch.setitem(settings.CIVIC, "VAPID_FILE", vapid_file)
    call_command("ensure_vapid")
    data = json.loads(vapid_file.read_text())
    assert data["public_key"]
    assert "PRIVATE KEY" in data["private_pem"]
    assert data["sub"].startswith("mailto:")
    assert vapid_file.stat().st_mode & 0o777 == 0o600


def test_ensure_vapid_est_idempotente(tmp_path, monkeypatch):
    """La perte des clés invaliderait tous les abonnements : jamais d'écrasement."""
    vapid_file = tmp_path / "vapid.json"
    monkeypatch.setitem(settings.CIVIC, "VAPID_FILE", vapid_file)
    call_command("ensure_vapid")
    avant = vapid_file.read_text()
    call_command("ensure_vapid")
    assert vapid_file.read_text() == avant
