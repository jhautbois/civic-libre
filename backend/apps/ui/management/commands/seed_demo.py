"""Données de démonstration : comptes, annonces, signalement d'exemple.

Double garde-fou contre toute exécution en production :
- refuse de s'exécuter si le domaine n'est pas en .localhost (un
  domaine .localhost ne résout qu'en boucle locale, RFC 6761 : les
  comptes de démonstration ne sont donc jamais joignables à distance) ;
- n'agit que si la base ne contient encore aucun utilisateur.
Activée par CIVIC_DEMO=1 dans l'entrypoint.
"""

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from apps.announcements.models import Announcement
from apps.reports import services
from apps.reports.models import Category, Department

DEMO_PASSWORD = "demo-civic-libre"  # noqa: S105 : inutilisable hors .localhost (garde ci-dessous)


class Command(BaseCommand):
    help = "Charge des données de démonstration (base vierge et domaine .localhost uniquement)."

    def handle(self, *args, **options):
        if not settings.CIVIC_DOMAIN.endswith(".localhost"):
            self.stdout.write(
                self.style.WARNING(
                    f"Graine de démonstration REFUSÉE : domaine « {settings.CIVIC_DOMAIN} » "
                    "hors .localhost. En production, créez le compte avec "
                    "createsuperuser (voir docs/exploitation/installation.md)."
                )
            )
            return
        if User.objects.exists():
            self.stdout.write("Des comptes existent déjà : graine de démonstration ignorée.")
            return

        admin = User.objects.create_superuser("maire", password=DEMO_PASSWORD)
        secretariat = User.objects.create_user("secretariat", password=DEMO_PASSWORD)
        secretariat.groups.add(Group.objects.get(name="gestionnaire"))
        agent = User.objects.create_user("agent-technique", password=DEMO_PASSWORD)
        agent.groups.add(Group.objects.get(name="agent"))
        agent.departments.add(Department.objects.get(name="Services techniques"))

        Announcement.objects.create(
            title="Bienvenue sur l'application de la commune",
            body="Retrouvez ici les actualités, l'agenda et le signalement de problèmes. "
            "Activez les notifications pour ne rien manquer.",
            is_pinned=True,
        )
        Announcement.objects.create(
            title="Coupure d'eau mercredi matin",
            body="Intervention sur le réseau entre 9h et 12h, secteur du bourg. "
            "Pensez à faire vos réserves.",
            level="alert",
        )

        services.create_report(
            category=Category.objects.get(code="eclairage"),
            description="Le lampadaire devant la salle des fêtes clignote depuis trois jours.",
            address="Place de la Mairie",
            location_hint="Côté salle des fêtes",
        )

        self.stdout.write(
            "Démo prête. Comptes (mot de passe : demo-civic-libre) : "
            "maire (admin), secretariat (gestionnaire), agent-technique (agent). "
            f"Superutilisateur : {admin.username}."
        )
