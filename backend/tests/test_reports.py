import io

import pytest
from django.core.exceptions import ValidationError
from PIL import Image

from apps.reports import geocoding, services
from apps.reports.images import reencode_image
from apps.reports.models import Category, Report, ReportPhoto


@pytest.fixture(autouse=True)
def _geocodage_hors_ligne(monkeypatch):
    monkeypatch.setattr(geocoding, "reverse", lambda lat, lon: "1 Place de la Mairie")
    monkeypatch.setattr(geocoding, "search", lambda q: (47.39, 0.69, "12 rue des Écoles"))


@pytest.fixture
def categorie(db):
    return Category.objects.get(code="voirie")


def _photo_avec_exif() -> io.BytesIO:
    """JPEG contenant des métadonnées EXIF (fabricant et orientation)."""
    image = Image.new("RGB", (800, 600), "grey")
    exif = Image.Exif()
    exif[0x010F] = "FabricantTest"  # Make
    exif[0x0112] = 6  # Orientation : couché, doit être redressé puis purgé
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    buffer.seek(0)
    buffer.name = "photo-test.jpg"
    buffer.size = buffer.getbuffer().nbytes
    return buffer


@pytest.mark.django_db
class TestService:
    def test_reference_sequentielle_par_annee(self, categorie):
        r1 = services.create_report(category=categorie, description="Trou", address="rue A")
        r2 = services.create_report(category=categorie, description="Bosse", address="rue B")
        year = r1.created_at.year
        assert r1.reference == f"R-{year}-0001"
        assert r2.reference == f"R-{year}-0002"
        assert r1.tracking_token != r2.tracking_token

    def test_geocodage_inverse_depuis_le_point(self, categorie):
        report = services.create_report(
            category=categorie, description="Trou", latitude=47.39, longitude=0.69
        )
        assert report.address == "1 Place de la Mairie"

    def test_geocodage_depuis_l_adresse(self, categorie):
        report = services.create_report(
            category=categorie, description="Trou", address="12 rue des Écoles"
        )
        assert report.latitude == pytest.approx(47.39)

    def test_sans_position_ni_adresse_refuse(self, categorie):
        with pytest.raises(ValidationError):
            services.create_report(category=categorie, description="Trou")

    def test_photo_reencodee_sans_exif(self, categorie):
        report = services.create_report(
            category=categorie,
            description="Dépôt sauvage",
            address="rue A",
            photo_file=_photo_avec_exif(),
        )
        photo = report.photos.get()
        cleaned = Image.open(photo.image.open("rb"))
        assert cleaned.format == "JPEG"
        assert not cleaned.getexif(), "les métadonnées EXIF doivent disparaître"
        assert photo.moderation_state == ReportPhoto.Moderation.PENDING


class TestImages:
    def test_fichier_non_image_refuse(self):
        fake = io.BytesIO(b"pas une image")
        fake.size = 12
        fake.name = "x.jpg"
        with pytest.raises(ValidationError):
            reencode_image(fake)

    def test_fichier_trop_lourd_refuse(self):
        big = io.BytesIO(b"x")
        big.size = 9 * 1024 * 1024
        with pytest.raises(ValidationError):
            reencode_image(big)


@pytest.mark.django_db
class TestParcours:
    def test_formulaire_accessible_sans_js(self, client):
        html = client.get("/signaler/").content.decode()
        assert "<fieldset" in html
        assert "Adresse ou lieu-dit" in html

    def test_depot_complet_puis_suivi(self, client, categorie):
        response = client.post(
            "/signaler/",
            {
                "category": categorie.pk,
                "description": "Lampadaire clignotant devant la salle des fêtes",
                "address": "12 rue des Écoles",
                "website": "",
            },
        )
        assert response.status_code == 302
        report = Report.objects.get()
        assert f"/suivi/{report.reference}/" in response["Location"]

        # Le déclarant (jeton) voit son contenu en attente de modération.
        page = client.get(response["Location"]).content.decode()
        assert "Lampadaire clignotant" in page
        assert "après vérification" in page

        # Un visiteur sans jeton ne voit que le statut.
        page = client.get(f"/suivi/{report.reference}/").content.decode()
        assert "Lampadaire clignotant" not in page
        assert "À traiter" in page

    def test_pot_de_miel(self, client, categorie):
        response = client.post(
            "/signaler/",
            {
                "category": categorie.pk,
                "description": "spam",
                "address": "x",
                "website": "http://spam.example",
            },
        )
        assert response.status_code == 200
        assert Report.objects.count() == 0

    def test_limitation_de_debit(self, client, categorie, settings):
        settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
        for i in range(5):
            client.post(
                "/signaler/",
                {
                    "category": categorie.pk,
                    "description": f"Problème {i}",
                    "address": "rue A",
                    "website": "",
                },
            )
        assert Report.objects.count() == 5
        response = client.post(
            "/signaler/",
            {
                "category": categorie.pk,
                "description": "Un de trop",
                "address": "rue A",
                "website": "",
            },
        )
        assert Report.objects.count() == 5
        assert "Trop de signalements" in response.content.decode()


@pytest.mark.django_db
class TestPhotoAcces:
    def _report_avec_photo(self, categorie):
        return services.create_report(
            category=categorie,
            description="Dépôt",
            address="rue A",
            photo_file=_photo_avec_exif(),
        )

    def test_photo_en_attente_inaccessible_sans_jeton(self, client, categorie):
        photo = self._report_avec_photo(categorie).photos.get()
        assert client.get(f"/signalements/photo/{photo.pk}/").status_code == 404

    def test_photo_accessible_avec_jeton(self, client, categorie):
        report = self._report_avec_photo(categorie)
        photo = report.photos.get()
        response = client.get(f"/signalements/photo/{photo.pk}/?jeton={report.tracking_token}")
        assert response.status_code == 200
        assert response["Content-Type"] == "image/jpeg"
