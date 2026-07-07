"""Client du géocodage national (Base Adresse Nationale, Géoplateforme IGN).

API compatible avec l'ancienne API Adresse (GeoJSON). Limite amont :
50 requêtes par seconde et par IP, très au delà des besoins d'une
commune. Tout échec est non bloquant : Open311 accepte address_string
OU lat/long, le signalement reste valide sans géocodage.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT_S = 5


def reverse(latitude: float, longitude: float) -> str:
    """Adresse la plus proche d'un point, ou chaîne vide."""
    try:
        response = requests.get(
            f"{settings.CIVIC['GEOCODING_URL']}/reverse",
            params={"lat": latitude, "lon": longitude, "limit": 1},
            timeout=TIMEOUT_S,
        )
        response.raise_for_status()
        features = response.json().get("features", [])
        return features[0]["properties"]["label"] if features else ""
    except Exception:  # noqa: BLE001
        logger.warning("Géocodage inverse indisponible pour %s,%s", latitude, longitude)
        return ""


def search(query: str) -> tuple[float, float, str] | None:
    """Premier résultat (latitude, longitude, libellé), ou None."""
    try:
        response = requests.get(
            f"{settings.CIVIC['GEOCODING_URL']}/search",
            params={"q": query, "limit": 1},
            timeout=TIMEOUT_S,
        )
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            return None
        lon, lat = features[0]["geometry"]["coordinates"]
        return lat, lon, features[0]["properties"]["label"]
    except Exception:  # noqa: BLE001
        logger.warning("Géocodage indisponible pour %r", query)
        return None
