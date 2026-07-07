"""API d'abonnement de la PWA (même origine, CSRF actif)."""

import json

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from apps.reports import throttle

from . import vapid
from .models import TOPICS, PushSubscription

VALID_TOPICS = {code for code, _ in TOPICS}


@require_GET
def public_key(request):
    return JsonResponse({"cle_publique": vapid.public_key()})


def _payload(request) -> dict | None:
    try:
        return json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


@require_POST
def subscribe(request):
    if not throttle.allow(request, "push", limit=30):
        return JsonResponse({"erreur": "trop de requêtes"}, status=429)
    data = _payload(request)
    if not data:
        return JsonResponse({"erreur": "corps JSON attendu"}, status=400)
    endpoint = (data.get("endpoint") or "")[:500]
    keys = data.get("keys") or {}
    topics = [t for t in (data.get("topics") or []) if t in VALID_TOPICS]
    if not endpoint.startswith("https://") or not keys.get("p256dh") or not keys.get("auth"):
        return JsonResponse({"erreur": "abonnement invalide"}, status=400)
    if not topics:
        topics = sorted(VALID_TOPICS)
    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "p256dh": keys["p256dh"][:200],
            "auth": keys["auth"][:100],
            "topics": topics,
            "failure_count": 0,
        },
    )
    return JsonResponse({"ok": True, "topics": topics})


@require_POST
def unsubscribe(request):
    data = _payload(request)
    endpoint = (data or {}).get("endpoint", "")
    deleted, _ = PushSubscription.objects.filter(endpoint=endpoint).delete()
    return JsonResponse({"ok": True, "supprime": bool(deleted)})
