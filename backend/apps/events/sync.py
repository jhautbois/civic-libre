"""Synchronisation du miroir local depuis Gancio (tâche de la boucle lente)."""

import logging

from . import gancio
from .models import MirroredEvent

logger = logging.getLogger(__name__)

MIRROR_FIELDS = [
    "title",
    "description",
    "starts_at",
    "ends_at",
    "place_name",
    "place_address",
    "tags",
    "image_url",
    "image_alt",
    "source_url",
]


def sync_gancio_events():
    """Upsert des événements de la fenêtre, suppression de ceux disparus.

    Le champ ``notified`` est préservé lors des mises à jour : une
    modification d'événement ne déclenche pas de seconde notification.
    """
    raw_events = gancio.fetch_raw_events()
    events = gancio.parse_events(raw_events)
    slugs = {e.get("id"): e.get("slug") for e in raw_events if isinstance(e, dict)}
    seen_ids = set()
    created = updated = 0

    for data in events:
        seen_ids.add(data["gancio_id"])
        slug = slugs.get(data["gancio_id"]) or data["gancio_id"]
        data["description"] = gancio.fetch_event_description(slug) or data["description"]
        _, was_created = MirroredEvent.objects.update_or_create(
            gancio_id=data["gancio_id"],
            defaults={field: data[field] for field in MIRROR_FIELDS},
        )
        if was_created:
            created += 1
        else:
            updated += 1

    deleted, _ = MirroredEvent.objects.exclude(gancio_id__in=seen_ids).delete()
    logger.info(
        "Synchronisation Gancio : %d créés, %d mis à jour, %d supprimés",
        created,
        updated,
        deleted,
    )
