"""Courriels du circuit de signalement.

Règle RGPD (docs/spec.md) : les courriels vers les services municipaux
ne contiennent JAMAIS les données du déclarant, seulement la référence,
la catégorie et un lien vers le back-office.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send(subject: str, body: str, recipient: str):
    if not recipient:
        return
    try:
        send_mail(subject, body, None, [recipient], fail_silently=False)
    except Exception:  # noqa: BLE001 : un SMTP en panne ne doit pas casser le parcours
        logger.exception("Envoi de courriel impossible vers %s", recipient)


def notify_department(report):
    department = report.category.department
    url = f"https://{settings.CIVIC_DOMAIN}/gestion/signalements/{report.reference}/"
    _send(
        f"[{settings.CIVIC['COMMUNE_NAME']}] Nouveau signalement {report.reference}",
        f"Un signalement vient d'être déposé.\n\n"
        f"Référence : {report.reference}\n"
        f"Catégorie : {report.category.name}\n\n"
        f"Le traiter : {url}\n",
        department.notification_email,
    )


def notify_reporter(report, update):
    if not report.reporter_email:
        return
    url = (
        f"https://{settings.CIVIC_DOMAIN}{report.get_absolute_url()}?jeton={report.tracking_token}"
    )
    lines = [
        f"Votre signalement {report.reference} ({report.category.name}) "
        f"est maintenant : {update.get_new_status_display().lower()}.",
    ]
    if update.public_comment:
        lines.append(f"\nMessage de la mairie : {update.public_comment}")
    if report.status == report.Status.REJECTED and report.rejection_reason:
        lines.append(f"\nMotif : {report.rejection_reason}")
    lines.append(f"\nSuivre votre signalement : {url}")
    lines.append("\nVous recevez ce courriel car vous l'avez demandé lors du dépôt.")
    _send(
        f"[{settings.CIVIC['COMMUNE_NAME']}] Signalement {report.reference} : "
        f"{update.get_new_status_display()}",
        "\n".join(lines),
        report.reporter_email,
    )
