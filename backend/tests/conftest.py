import pytest


@pytest.fixture(autouse=True)
def _static_storage_simple(settings):
    """En test, pas de manifeste whitenoise : les statiques ne sont pas collectés."""
    settings.STORAGES["staticfiles"]["BACKEND"] = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
