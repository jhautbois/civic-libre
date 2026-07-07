"""Génère la paire de clés VAPID au premier démarrage, sans jamais l'écraser.

La perte de la clé privée invaliderait silencieusement tous les
abonnements push des habitants : le fichier fait partie du périmètre
de sauvegarde obligatoire (docs/exploitation/).
"""

import base64
import json

from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.core.management.base import BaseCommand
from py_vapid import Vapid


class Command(BaseCommand):
    help = "Crée le fichier de clés VAPID s'il n'existe pas déjà (idempotent)."

    def handle(self, *args, **options):
        vapid_file = settings.CIVIC["VAPID_FILE"]
        if vapid_file.exists():
            self.stdout.write(f"Clés VAPID déjà présentes : {vapid_file}")
            return

        vapid = Vapid()
        vapid.generate_keys()
        raw_public = vapid.public_key.public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
        )
        payload = {
            "public_key": base64.urlsafe_b64encode(raw_public).rstrip(b"=").decode(),
            "private_pem": vapid.private_pem().decode(),
            "sub": f"mailto:{settings.DEFAULT_FROM_EMAIL}",
        }
        vapid_file.parent.mkdir(parents=True, exist_ok=True)
        vapid_file.write_text(json.dumps(payload, indent=2))
        vapid_file.chmod(0o600)
        self.stdout.write(f"Clés VAPID générées : {vapid_file}")
