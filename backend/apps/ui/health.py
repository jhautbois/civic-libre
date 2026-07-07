"""Endpoint de santé pour la supervision (voir docs/architecture.md).

Agrège l'état des composants observables depuis le cœur. Le worker
écrit un fichier heartbeat à chaque tour de sa boucle courte ; son âge
est le signal principal de vie des tâches de fond.
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


def _heartbeat_age() -> int | None:
    heartbeat = settings.CIVIC["HEARTBEAT_FILE"]
    if not heartbeat.exists():
        return None
    return int(time.time() - heartbeat.stat().st_mtime)


def sante(request):
    disk = shutil.disk_usage(settings.DATA_DIR)
    payload = {
        "db": _db_ok(),
        "disk_free_mb": disk.free // (1024 * 1024),
        "worker_heartbeat_age_s": _heartbeat_age(),
    }
    status = 200 if payload["db"] == "ok" else 503
    return JsonResponse(payload, status=status)
