"""Détection des nouveautés et envoi de l'outbox (boucles du worker).

Contrat (docs/adr/0005) : les alertes partent avant tout, envoi
parallèle borné, purge des abonnements sur 404/410, reprise sans
doublon après interruption, backoff exponentiel par livraison.
"""

import datetime
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from django.utils import timezone
from pywebpush import WebPushException, webpush

from apps.announcements.models import Announcement
from apps.events.models import MirroredEvent

from . import vapid
from .models import NotificationDelivery, OutgoingNotification, PushSubscription

logger = logging.getLogger(__name__)

POOL_SIZE = 8
TTL_BY_PRIORITY = {"alert": 3600, "normal": 86400}
MAX_ATTEMPTS = 3
STUCK_AFTER = datetime.timedelta(minutes=5)
PURGE_AFTER_FAILURES = 10


def scan_announcements():
    """Une annonce devenue visible déclenche une notification, une fois."""
    for announcement in Announcement.objects.visible().filter(notified=False):
        is_alert = announcement.level == Announcement.Level.ALERT
        OutgoingNotification.objects.create(
            topic="alerts" if is_alert else "news",
            priority="alert" if is_alert else "normal",
            title=("Alerte : " if is_alert else "") + announcement.title[:100],
            body=announcement.body[:200],
            url=announcement.get_absolute_url(),
        )
        announcement.notified = True
        announcement.save(update_fields=["notified"])


def scan_events():
    """Un nouvel événement à venir déclenche une notification, une fois.

    Le champ notified est préservé par la synchronisation : une simple
    édition dans Gancio ne renotifie jamais.
    """
    for event in MirroredEvent.objects.filter(notified=False, starts_at__gte=timezone.now()):
        OutgoingNotification.objects.create(
            topic="events",
            title=f"Nouvel événement : {event.title}"[:120],
            body=timezone.localtime(event.starts_at).strftime("%d/%m/%Y à %H:%M")
            + (f" · {event.place_name}" if event.place_name else ""),
            url=event.get_absolute_url(),
        )
        event.notified = True
        event.save(update_fields=["notified"])


def send_pending():
    _requeue_stuck()
    pending = list(
        OutgoingNotification.objects.filter(state=OutgoingNotification.State.PENDING).order_by(
            "-priority",
            "created_at",  # 'alert' < 'normal' alphabétiquement : ordre inversé voulu
        )
    )
    pending.sort(key=lambda n: (n.priority != "alert", n.created_at))
    for notification in pending:
        _send_one(notification)


def _requeue_stuck():
    limit = timezone.now() - STUCK_AFTER
    OutgoingNotification.objects.filter(
        state=OutgoingNotification.State.SENDING, created_at__lt=limit
    ).update(state=OutgoingNotification.State.PENDING)


def _send_one(notification):
    notification.state = OutgoingNotification.State.SENDING
    notification.save(update_fields=["state"])

    # Livraisons créées une seule fois par abonnement (contrainte unique).
    for subscription in PushSubscription.objects.filter(topics__icontains=notification.topic):
        NotificationDelivery.objects.get_or_create(
            notification=notification, subscription=subscription
        )

    now = timezone.now()
    todo = [
        delivery
        for delivery in notification.deliveries.select_related("subscription").exclude(
            state__in=[NotificationDelivery.State.SENT, NotificationDelivery.State.GONE]
        )
        if delivery.attempts < MAX_ATTEMPTS and _backoff_elapsed(delivery, now)
    ]

    with ThreadPoolExecutor(max_workers=POOL_SIZE) as pool:
        results = list(pool.map(_deliver, todo))

    for delivery, outcome in zip(todo, results, strict=True):
        _record(delivery, outcome)

    remaining = notification.deliveries.filter(
        state__in=[NotificationDelivery.State.PENDING, NotificationDelivery.State.FAILED],
        attempts__lt=MAX_ATTEMPTS,
    ).exists()
    if remaining:
        notification.state = OutgoingNotification.State.PENDING
    else:
        notification.state = OutgoingNotification.State.DONE
        notification.sent_at = timezone.now()
    notification.save(update_fields=["state", "sent_at"])


def _backoff_elapsed(delivery, now):
    if not delivery.last_attempt_at:
        return True
    wait = datetime.timedelta(seconds=60 * (2**delivery.attempts))
    return now - delivery.last_attempt_at >= wait


def _deliver(delivery) -> str:
    subscription = delivery.subscription
    payload = json.dumps(
        {
            "title": delivery.notification.title,
            "body": delivery.notification.body,
            "url": delivery.notification.url,
        },
        ensure_ascii=False,
    )
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=payload,
            vapid_private_key=vapid.private_pem(),
            vapid_claims=dict(vapid.claims()),
            ttl=TTL_BY_PRIORITY[delivery.notification.priority],
            headers={"Urgency": "high"} if delivery.notification.priority == "alert" else None,
        )
        return "sent"
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            return "gone"
        logger.warning("Échec push (%s) : %s", status, exc)
        return "failed"
    except Exception:  # noqa: BLE001
        logger.exception("Échec push inattendu")
        return "failed"


def _record(delivery, outcome):
    delivery.attempts += 1
    delivery.last_attempt_at = timezone.now()
    subscription = delivery.subscription
    if outcome == "sent":
        delivery.state = NotificationDelivery.State.SENT
        subscription.last_success_at = timezone.now()
        subscription.failure_count = 0
        subscription.save(update_fields=["last_success_at", "failure_count"])
    elif outcome == "gone":
        delivery.state = NotificationDelivery.State.GONE
        delivery.save()
        subscription.delete()
        return
    else:
        delivery.state = NotificationDelivery.State.FAILED
        subscription.failure_count += 1
        subscription.save(update_fields=["failure_count"])
    delivery.save()


def purge_dead_subscriptions():
    """Abonnements en échec persistant : purge RGPD (docs/spec.md)."""
    six_months_ago = timezone.now() - datetime.timedelta(days=180)
    PushSubscription.objects.filter(
        failure_count__gte=PURGE_AFTER_FAILURES, created_at__lt=six_months_ago
    ).exclude(last_success_at__gte=six_months_ago).delete()
