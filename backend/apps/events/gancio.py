"""Client de lecture de l'API publique Gancio.

Surface consommée volontairement minimale (docs/adr/0003) :
``GET /api/events`` avec fenêtre temporelle. Toute évolution amont est
détectée par les tests de contrat ; le repli documenté est le parsing
du flux iCal.
"""

import datetime
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

WINDOW_PAST_DAYS = 30
WINDOW_FUTURE_DAYS = 180
TIMEOUT_S = 15


def fetch_raw_events() -> list[dict]:
    """Interroge Gancio sur la fenêtre glissante et renvoie le JSON brut."""
    now = datetime.datetime.now(datetime.UTC)
    params = {
        "start": int((now - datetime.timedelta(days=WINDOW_PAST_DAYS)).timestamp()),
        "end": int((now + datetime.timedelta(days=WINDOW_FUTURE_DAYS)).timestamp()),
        "show_recurrent": "true",
    }
    response = requests.get(
        f"{settings.CIVIC['GANCIO_API_URL']}/api/events", params=params, timeout=TIMEOUT_S
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"Réponse inattendue de l'API Gancio : {type(payload)}")
    return payload


def fetch_event_description(slug_or_id) -> str:
    """La liste /api/events ne renvoie pas la description : appel détail.

    Toute erreur est non bloquante (la synchronisation garde les autres
    champs), le champ sera réessayé au prochain passage.
    """
    try:
        response = requests.get(
            f"{settings.CIVIC['GANCIO_API_URL']}/api/event/detail/{slug_or_id}",
            timeout=TIMEOUT_S,
        )
        response.raise_for_status()
        return (response.json().get("description") or "").strip()
    except Exception:  # noqa: BLE001
        logger.warning("Description indisponible pour l'événement %s", slug_or_id)
        return ""


def parse_event(raw: dict) -> dict | None:
    """Normalise un événement Gancio ; renvoie None si inexploitable."""
    gancio_id = raw.get("id")
    title = (raw.get("title") or "").strip()
    start = raw.get("start_datetime")
    if not gancio_id or not title or not start:
        return None

    public_base = settings.CIVIC["AGENDA_URL"].rstrip("/")
    place = raw.get("place") or {}
    media = raw.get("media") or []
    image_url = ""
    image_alt = ""
    if media and isinstance(media, list) and media[0].get("url"):
        image_url = f"{public_base}/media/thumb/{media[0]['url']}"
        image_alt = (media[0].get("name") or "").strip()

    end = raw.get("end_datetime")
    return {
        "gancio_id": gancio_id,
        "title": title[:200],
        "description": (raw.get("description") or "").strip(),
        "starts_at": datetime.datetime.fromtimestamp(start, tz=datetime.UTC),
        "ends_at": datetime.datetime.fromtimestamp(end, tz=datetime.UTC) if end else None,
        "place_name": (place.get("name") or "")[:200],
        "place_address": (place.get("address") or "")[:300],
        "tags": [str(t) for t in (raw.get("tags") or [])],
        "image_url": image_url[:500],
        "image_alt": image_alt[:300],
        "source_url": f"{public_base}/event/{raw.get('slug') or gancio_id}"[:500],
    }


def parse_events(payload: list[dict]) -> list[dict]:
    events = []
    for raw in payload:
        parsed = parse_event(raw)
        if parsed is None:
            logger.warning("Événement Gancio ignoré (champs manquants) : %r", raw.get("id"))
        else:
            events.append(parsed)
    return events
