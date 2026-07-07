"""Registres des tâches du worker.

Chaque application ajoute ses tâches ici, explicitement, pour que la
liste complète reste lisible d'un coup d'œil (voir docs/adr/0005).
Une tâche est un simple appelable sans argument ; le worker isole les
exceptions et journalise.
"""

from apps.events.sync import sync_gancio_events
from apps.push.sender import (
    purge_dead_subscriptions,
    scan_announcements,
    scan_events,
    send_pending,
)

SHORT_TASKS: list = [
    scan_announcements,  # une alerte publiée part en moins de 10 secondes
    send_pending,
]

LONG_TASKS: list = [
    sync_gancio_events,
    scan_events,
    purge_dead_subscriptions,
    # Lot 8 : anonymisation planifiée des signalements.
]
