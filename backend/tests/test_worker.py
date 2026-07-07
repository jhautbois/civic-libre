from django.conf import settings
from django.core.management import call_command

from apps.ui import tasks


def test_run_worker_once_ecrit_le_heartbeat(tmp_path, monkeypatch):
    heartbeat = tmp_path / "worker-heartbeat"
    monkeypatch.setitem(settings.CIVIC, "HEARTBEAT_FILE", heartbeat)
    call_command("run_worker", once=True)
    assert heartbeat.exists()


def test_run_worker_execute_les_registres(tmp_path, monkeypatch):
    monkeypatch.setitem(settings.CIVIC, "HEARTBEAT_FILE", tmp_path / "hb")
    appels = []
    monkeypatch.setattr(tasks, "SHORT_TASKS", [lambda: appels.append("courte")])
    monkeypatch.setattr(tasks, "LONG_TASKS", [lambda: appels.append("longue")])
    call_command("run_worker", once=True)
    assert appels == ["courte", "longue"]


def test_run_worker_isole_les_exceptions(tmp_path, monkeypatch):
    """Une tâche qui lève ne doit pas empêcher les suivantes ni le heartbeat."""
    heartbeat = tmp_path / "hb"
    monkeypatch.setitem(settings.CIVIC, "HEARTBEAT_FILE", heartbeat)
    appels = []

    def explose():
        raise RuntimeError("panne simulée")

    monkeypatch.setattr(tasks, "SHORT_TASKS", [explose, lambda: appels.append("suivante")])
    monkeypatch.setattr(tasks, "LONG_TASKS", [])
    call_command("run_worker", once=True)
    assert appels == ["suivante"]
    assert heartbeat.exists()
