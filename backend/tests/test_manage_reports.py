import pytest
from django.contrib.auth.models import Group, User
from django.core import mail

from apps.reports import services
from apps.reports.models import Category, Department, Report


@pytest.fixture(autouse=True)
def _geocodage_hors_ligne(monkeypatch):
    from apps.reports import geocoding

    monkeypatch.setattr(geocoding, "reverse", lambda lat, lon: "")
    monkeypatch.setattr(geocoding, "search", lambda q: None)


@pytest.fixture
def agent(client, db):
    user = User.objects.create_user("agent-voirie", password="motdepasse-test")
    user.groups.add(Group.objects.get(name="agent"))
    user.departments.add(Department.objects.get(name="Services techniques"))
    client.login(username="agent-voirie", password="motdepasse-test")
    return user


@pytest.fixture
def report(db):
    return services.create_report(
        category=Category.objects.get(code="voirie"),
        description="Trou dangereux devant l'école",
        address="12 rue des Écoles",
        reporter_email="habitant@example.org",
    )


@pytest.mark.django_db
class TestNotificationServiceMunicipal:
    def test_courriel_sans_donnees_personnelles(self, django_capture_on_commit_callbacks):
        department = Department.objects.get(name="Services techniques")
        department.notification_email = "voirie@mairie.example"
        department.save()
        with django_capture_on_commit_callbacks(execute=True):
            services.create_report(
                category=Category.objects.get(code="voirie"),
                description="Trou dangereux",
                address="12 rue des Écoles",
                reporter_email="habitant@example.org",
            )
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == ["voirie@mairie.example"]
        assert "habitant@example.org" not in message.body
        assert "Trou dangereux" not in message.body
        assert "R-" in message.body


@pytest.mark.django_db
class TestFile:
    def test_acces_reserve(self, client, report):
        assert client.get("/gestion/signalements/").status_code == 302

    def test_file_agent(self, client, agent, report):
        html = client.get("/gestion/signalements/").content.decode()
        assert report.reference in html

    def test_detail_montre_tout_a_l_agent(self, client, agent, report):
        html = client.get(f"/gestion/signalements/{report.reference}/").content.decode()
        assert "Trou dangereux" in html
        assert "declarant joignable" in html or "déclarant joignable" in html


@pytest.mark.django_db
class TestTransition:
    def test_cycle_complet_avec_courriels(
        self, client, agent, report, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            client.post(
                f"/gestion/signalements/{report.reference}/statut/",
                {"new_status": "in_progress", "public_comment": "Intervention prévue mardi."},
            )
        report.refresh_from_db()
        assert report.status == "in_progress"
        assert report.closed_at is None

        with django_capture_on_commit_callbacks(execute=True):
            client.post(
                f"/gestion/signalements/{report.reference}/statut/",
                {"new_status": "resolved", "public_comment": "Rebouché."},
            )
        report.refresh_from_db()
        assert report.status == "resolved"
        assert report.closed_at is not None
        assert report.updates.count() == 2

        courriels = [m for m in mail.outbox if m.to == ["habitant@example.org"]]
        assert len(courriels) == 2
        assert "jeton=" in courriels[-1].body
        assert "Rebouché." in courriels[-1].body

    def test_rejet_exige_un_motif(self, client, agent, report):
        client.post(
            f"/gestion/signalements/{report.reference}/statut/",
            {"new_status": "rejected", "rejection_reason": ""},
        )
        report.refresh_from_db()
        assert report.status == "new"

    def test_l_historique_apparait_sur_le_suivi_public(self, client, agent, report):
        client.post(
            f"/gestion/signalements/{report.reference}/statut/",
            {"new_status": "in_progress", "public_comment": "Vu, nous intervenons rapidement."},
        )
        client.logout()
        html = client.get(f"/suivi/{report.reference}/").content.decode()
        assert "En cours" in html
        assert "Vu, nous intervenons rapidement." in html


@pytest.mark.django_db
class TestModeration:
    def test_publication_rend_le_contenu_visible(self, client, agent, report):
        client.post(f"/gestion/signalements/{report.reference}/moderation/", {"action": "publier"})
        client.logout()
        html = client.get(f"/suivi/{report.reference}/").content.decode()
        assert "Trou dangereux" in html

    def test_file_filtre_par_statut(self, client, agent, report):
        services.transition_report(
            report=Report.objects.get(pk=report.pk),
            new_status="resolved",
            author=agent,
        )
        html = client.get("/gestion/signalements/?statut=ouverts").content.decode()
        assert report.reference not in html
        html = client.get("/gestion/signalements/?statut=resolved").content.decode()
        assert report.reference in html
