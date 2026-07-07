"""Limitation de débit simple, adossée au cache partagé (base SQLite).

L'adresse IP sert uniquement de clef de fenêtre glissante, elle n'est
pas journalisée ici (voir docs/spec.md, sécurité et RGPD).
"""

from django.core.cache import cache

WINDOW_S = 3600
MAX_PER_WINDOW = 5


def client_ip(request) -> str | None:
    """Derrière Caddy, la dernière entrée de X-Forwarded-For est posée
    par le proxy lui-même : c'est la seule fiable."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR")


def allow(request, action: str, limit: int = MAX_PER_WINDOW) -> bool:
    ip = client_ip(request) or "inconnue"
    key = f"throttle:{action}:{ip}"
    added = cache.add(key, 1, timeout=WINDOW_S)
    if added:
        return True
    try:
        count = cache.incr(key)
    except ValueError:  # clef expirée entre temps
        cache.add(key, 1, timeout=WINDOW_S)
        return True
    return count <= limit
