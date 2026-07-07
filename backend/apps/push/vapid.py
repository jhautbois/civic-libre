import json
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def keys() -> dict:
    """Clés VAPID générées par ensure_vapid au premier démarrage."""
    return json.loads(settings.CIVIC["VAPID_FILE"].read_text())


def public_key() -> str:
    return keys()["public_key"]


def private_pem() -> str:
    return keys()["private_pem"]


def claims() -> dict:
    return {"sub": keys()["sub"]}
