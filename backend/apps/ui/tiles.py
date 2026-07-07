"""Proxy de tuiles cartographiques avec cache disque.

L'adresse IP des habitants ne part jamais chez le fournisseur de
tuiles (exigence RGPD de la spec), la CSP reste same-origin, et le
cache local respecte la politique d'usage des serveurs communautaires
(conservation 7 jours minimum). Fournisseur configurable
(CIVIC_TILES_URL), purge par le worker (lot 8).
"""

import logging
import time

import requests
from django.conf import settings
from django.http import Http404, HttpResponse

logger = logging.getLogger(__name__)

MAX_ZOOM = 19
CACHE_MAX_AGE_S = 7 * 24 * 3600
TIMEOUT_S = 10
USER_AGENT = "CivicLibre/0.1 (+https://civic.localhost)"


def tile(request, z: int, x: int, y: int):
    if not (0 <= z <= MAX_ZOOM and 0 <= x < 2**z and 0 <= y < 2**z):
        raise Http404

    cache_path = settings.DATA_DIR / "tiles" / str(z) / str(x) / f"{y}.png"
    if cache_path.exists() and time.time() - cache_path.stat().st_mtime < CACHE_MAX_AGE_S:
        content = cache_path.read_bytes()
    else:
        url = settings.CIVIC["TILES_URL"].format(z=z, x=x, y=y)
        try:
            upstream = requests.get(url, timeout=TIMEOUT_S, headers={"User-Agent": USER_AGENT})
            upstream.raise_for_status()
            content = upstream.content
        except Exception:  # noqa: BLE001
            logger.warning("Tuile indisponible : %s/%s/%s", z, x, y)
            if cache_path.exists():
                content = cache_path.read_bytes()  # cache périmé plutôt que trou
            else:
                raise Http404 from None
        else:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(content)

    response = HttpResponse(content, content_type="image/png")
    response["Cache-Control"] = f"public, max-age={CACHE_MAX_AGE_S}"
    return response
