from django.conf import settings


def test_locale_francaise():
    assert settings.LANGUAGE_CODE == "fr"
    assert settings.TIME_ZONE == "Europe/Paris"
    assert settings.USE_TZ is True


def test_argon2_prioritaire():
    assert "Argon2" in settings.PASSWORD_HASHERS[0]


def test_sqlite_wal_et_verrous():
    options = settings.DATABASES["default"]["OPTIONS"]
    assert "journal_mode=WAL" in options["init_command"]
    assert "busy_timeout" in options["init_command"]
    assert options["transaction_mode"] == "IMMEDIATE"
