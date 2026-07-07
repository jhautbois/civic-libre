"""Endpoint de santé pour la supervision (voir docs/architecture.md).

Agrège l'état des composants observables : base, disque, worker
(heartbeat), synchronisation Gancio, notifications en attente et âge
de la dernière sauvegarde (marqueur déposé par le script).
"""

import shutil
import time

from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def _db_ok() -> str:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return "ok"
    except Exception:  # noqa: BLE001 : l'endpoint de santé ne doit jamais lever
        return "erreur"


def _file_age(path) -> int | None:
    if not path.exists():
        return None
    return int(time.time() - path.stat().st_mtime)


def _sync_age() -> int | None:
    from apps.events.models import MirroredEvent

    try:
        latest = MirroredEvent.objects.order_by("-synced_at").first()
    except Exception:  # noqa: BLE001
        return None
    if latest is None:
        return None
    return int(time.time() - latest.synced_at.timestamp())


def _outbox_pending() -> int | None:
    from apps.push.models import OutgoingNotification

    try:
        return OutgoingNotification.objects.filter(
            state=OutgoingNotification.State.PENDING
        ).count()
    except Exception:  # noqa: BLE001
        return None


def sante(request):
    disk = shutil.disk_usage(settings.DATA_DIR)
    payload = {
        "db": _db_ok(),
        "disk_free_mb": disk.free // (1024 * 1024),
        "worker_heartbeat_age_s": _file_age(settings.CIVIC["HEARTBEAT_FILE"]),
        "gancio_sync_age_s": _sync_age(),
        "notifications_en_attente": _outbox_pending(),
        "last_backup_age_s": _file_age(settings.DATA_DIR / "last-backup"),
    }
    status = 200 if payload["db"] == "ok" else 503
    return JsonResponse(payload, status=status)
