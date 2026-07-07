"""Anonymisation planifiée des signalements (docs/spec.md, RGPD).

Défauts : 12 mois après clôture, butoir absolu 24 mois après dépôt
quel que soit le statut. Sont purgés : courriel, jeton de suivi, IP et
user-agent (LCEN, 12 mois), photos (fichiers compris). Les données
techniques anonymes (catégorie, statut, dates, position) sont
conservées pour les statistiques.
"""

import datetime
import logging

from django.utils import timezone

from .models import Report

logger = logging.getLogger(__name__)

AFTER_CLOSURE = datetime.timedelta(days=365)
HARD_LIMIT = datetime.timedelta(days=730)


def anonymize_reports():
    now = timezone.now()
    due = Report.objects.filter(anonymized_at__isnull=True).filter(
        models_q_closed_before(now - AFTER_CLOSURE) | models_q_created_before(now - HARD_LIMIT)
    )
    count = 0
    for report in due:
        for photo in report.photos.all():
            photo.image.delete(save=False)
            photo.thumbnail.delete(save=False)
            photo.delete()
        report.reporter_email = ""
        report.tracking_token = ""
        report.created_ip = None
        report.created_user_agent = ""
        report.anonymized_at = now
        report.save(
            update_fields=[
                "reporter_email",
                "tracking_token",
                "created_ip",
                "created_user_agent",
                "anonymized_at",
            ]
        )
        count += 1
    if count:
        logger.info("Anonymisation : %d signalement(s)", count)


def models_q_closed_before(limit):
    from django.db.models import Q

    return Q(closed_at__isnull=False, closed_at__lt=limit)


def models_q_created_before(limit):
    from django.db.models import Q

    return Q(created_at__lt=limit)
