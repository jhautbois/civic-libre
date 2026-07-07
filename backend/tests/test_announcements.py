import datetime

import pytest
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.announcements.models import Announcement


def _make(title="Travaux rue de l'Église", level="info", **kwargs):
    return Announcement.objects.create(title=title, body="Texte de l'annonce.",
                                       level=level, **kwargs)


@pytest.fixture
def gestionnaire(client):
    user = User.objects.create_user("secretariat", password="motdepasse-test")
    user.groups.add(Group.objects.get(name="gestionnaire"))
    client.login(username="secretariat", password="motdepasse-test")
    return user


@pytest.mark.django_db
class TestModele:
    def test_alt_obligatoire_si_image_informative(self):
        a = Announcement(
            title="Photo sans alternative",
            body="x",
            image="annonces/x.jpg",
            image_is_decorative=False,
            image_alt="",
        )
        with pytest.raises(ValidationError) as exc:
            a.full_clean()
        assert "image_alt" in exc.value.error_dict

    def test_alt_facultatif_si_decorative(self):
        a = Announcement(
            title="Photo décorative",
            body="x",
            image="annonces/x.jpg",
            image_is_decorative=True,
        )
        a.full_clean()  # ne lève pas

    def test_visibles_exclut_futures_et_expirees(self):
        _make(title="Visible")
        _make(title="Programmée", published_at=timezone.now() + datetime.timedelta(days=1))
        _make(
            title="Expirée",
            published_at=timezone.now() - datetime.timedelta(days=2),
            expires_at=timezone.now() - datetime.timedelta(days=1),
        )
        titles = {a.title for a in Announcement.objects.visible()}
        assert titles == {"Visible"}


@pytest.mark.django_db
class TestPublic:
    def test_fil_accueil_affiche_alerte_et_actualite(self, client):
        _make(title="Coupure du réseau mercredi", level="alert")
        _make(title="Nouveaux horaires de la mairie")
        html = client.get("/").content.decode()
        assert "Coupure du réseau mercredi" in html
        assert "Nouveaux horaires de la mairie" in html
        assert "Alerte" in html

    def test_detail_public(self, client):
        a = _make()
        assert client.get(a.get_absolute_url()).status_code == 200

    def test_annonce_programmee_invisible(self, client):
        a = _make(title="Future", published_at=timezone.now() + datetime.timedelta(days=1))
        assert client.get(a.get_absolute_url()).status_code == 404

    def test_rss_valide(self, client):
        _make(title="Alerte orage", level="alert")
        response = client.get("/flux/annonces.rss")
        assert response.status_code == 200
        import xml.dom.minidom

        doc = xml.dom.minidom.parseString(response.content)
        titre = doc.getElementsByTagName("item")[0].getElementsByTagName("title")[0]
        assert titre.firstChild.data == "[Alerte] Alerte orage"


@pytest.mark.django_db
class TestGestion:
    def test_anonyme_redirige_vers_connexion(self, client):
        response = client.get("/gestion/annonces/")
        assert response.status_code == 302
        assert "/gestion/connexion/" in response["Location"]

    def test_gestionnaire_cree_une_annonce(self, client, gestionnaire):
        response = client.post(
            "/gestion/annonces/nouvelle/",
            {
                "title": "Inscriptions cantine",
                "body": "Les inscriptions ouvrent lundi.",
                "level": "info",
                "published_at": timezone.now().strftime("%Y-%m-%dT%H:%M"),
            },
        )
        assert response.status_code == 302, response.context["form"].errors
        annonce = Announcement.objects.get(title="Inscriptions cantine")
        assert annonce.created_by == gestionnaire

    def test_utilisateur_sans_droit_interdit(self, client):
        User.objects.create_user("intrus", password="motdepasse-test")
        client.login(username="intrus", password="motdepasse-test")
        assert client.get("/gestion/annonces/").status_code == 403
