import pytest


@pytest.fixture(autouse=True)
def _static_sans_manifeste(settings):
    """En test, pas de manifeste whitenoise (statiques non collectés) ;
    les fichiers sont servis directement depuis les apps (finders)."""
    settings.STORAGES["staticfiles"]["BACKEND"] = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    settings.WHITENOISE_USE_FINDERS = True
    settings.WHITENOISE_AUTOREFRESH = True
