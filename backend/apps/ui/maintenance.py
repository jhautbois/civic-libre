"""Tâches d'exploitation : purge du cache de tuiles, alerte exploitant.

L'alerte courriel vers CIVIC_OPERATOR_EMAIL est limitée à une par jour
et par motif (cache partagé), pour signaler sans harceler.
"""

import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)

TILE_MAX_AGE_S = 14 * 24 * 3600
BACKUP_MAX_AGE_S = 48 * 3600


def purge_tile_cache():
    tiles_dir = settings.DATA_DIR / "tiles"
    if not tiles_dir.exists():
        return
    limit = time.time() - TILE_MAX_AGE_S
    for tile in tiles_dir.rglob("*.png"):
        if tile.stat().st_mtime < limit:
            tile.unlink(missing_ok=True)


def _alert_operator(reason_key: str, subject: str, body: str):
    recipient = settings.CIVIC["OPERATOR_EMAIL"]
    if not recipient:
        return
    if not cache.add(f"alerte-exploitant:{reason_key}", 1, timeout=24 * 3600):
        return
    try:
        send_mail(f"[Civic Libre] {subject}", body, None, [recipient], fail_silently=False)
    except Exception:  # noqa: BLE001
        logger.exception("Alerte exploitant impossible (%s)", reason_key)


def check_backup_age():
    """Le script de sauvegarde dépose un marqueur ; trop vieux = alerte."""
    marker = settings.DATA_DIR / "last-backup"
    if not marker.exists():
        _alert_operator(
            "sauvegarde-absente",
            "Aucune sauvegarde détectée",
            "Aucune sauvegarde n'a encore été enregistrée sur cette instance.\n"
            "Voir docs/exploitation/exploitation.md (section sauvegardes).",
        )
        return
    age = time.time() - marker.stat().st_mtime
    if age > BACKUP_MAX_AGE_S:
        _alert_operator(
            "sauvegarde-vieille",
            "Sauvegarde trop ancienne",
            f"La dernière sauvegarde date de {int(age / 3600)} heures "
            f"(seuil : 48 h). Vérifiez la tâche cron de sauvegarde.",
        )


def check_outbox_stuck():
    from apps.push.models import OutgoingNotification

    stuck = OutgoingNotification.objects.filter(
        state=OutgoingNotification.State.PENDING,
        created_at__lt=timezone.now() - timezone.timedelta(hours=1),
    ).count()
    if stuck:
        _alert_operator(
            "outbox-bloquee",
            "Notifications en attente depuis plus d'une heure",
            f"{stuck} notification(s) n'ont pas pu partir depuis plus d'une heure. "
            "Vérifiez le worker (docker compose logs worker) et /sante.",
        )
