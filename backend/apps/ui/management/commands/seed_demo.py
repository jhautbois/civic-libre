"""Données de démonstration : comptes, annonces, signalement d'exemple.

N'agit que si la base ne contient encore aucun utilisateur (jamais en
production). Activée par CIVIC_DEMO=1 dans l'entrypoint.
"""

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from apps.announcements.models import Announcement
from apps.reports import services
from apps.reports.models import Category, Department

DEMO_PASSWORD = "demo-civic-libre"  # noqa: S105 : démonstration locale uniquement


class Command(BaseCommand):
    help = "Charge des données de démonstration (uniquement sur base vierge)."

    def handle(self, *args, **options):
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
