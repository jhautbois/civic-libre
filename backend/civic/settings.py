"""Réglages Django de Civic Libre.

Tout est piloté par des variables d'environnement CIVIC_* documentées
dans .env.example à la racine du dépôt. Les valeurs par défaut donnent
un environnement de développement et de démonstration fonctionnel.
"""

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("CIVIC_DATA_DIR", BASE_DIR / ".data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "media").mkdir(exist_ok=True)
(DATA_DIR / "db").mkdir(exist_ok=True)
(DATA_DIR / "static").mkdir(exist_ok=True)


def _secret_key() -> str:
    """Clé lue dans l'environnement, sinon générée une fois et persistée."""
    from_env = os.environ.get("CIVIC_SECRET_KEY")
    if from_env:
        return from_env
    key_file = DATA_DIR / "secret_key"
    if not key_file.exists():
        key_file.write_text(secrets.token_urlsafe(64))
        key_file.chmod(0o600)
    return key_file.read_text().strip()


SECRET_KEY = _secret_key()

DEBUG = os.environ.get("CIVIC_DEBUG", "0") == "1"

CIVIC_DOMAIN = os.environ.get("CIVIC_DOMAIN", "civic.localhost")
CIVIC_AGENDA_DOMAIN = os.environ.get("CIVIC_AGENDA_DOMAIN", f"agenda.{CIVIC_DOMAIN}")

ALLOWED_HOSTS = [CIVIC_DOMAIN, "localhost", "127.0.0.1", "core"]
CSRF_TRUSTED_ORIGINS = [f"https://{CIVIC_DOMAIN}"]

# Réglages propres à la commune (affichage, intégrations).
CIVIC = {
    "COMMUNE_NAME": os.environ.get("CIVIC_COMMUNE_NAME", "Villebourg"),
    "ACCENT_COLOR": os.environ.get("CIVIC_ACCENT_COLOR", "#31597F"),
    "AGENDA_URL": f"https://{CIVIC_AGENDA_DOMAIN}",
    "GANCIO_API_URL": os.environ.get("GANCIO_API_URL", "http://gancio:13120"),
    "GEOCODING_URL": os.environ.get("CIVIC_GEOCODING_URL", "https://data.geopf.fr/geocodage"),
    "TILES_URL": os.environ.get(
        "CIVIC_TILES_URL", "https://tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png"
    ),
    "OPERATOR_EMAIL": os.environ.get("CIVIC_OPERATOR_EMAIL", ""),
    "VAPID_FILE": DATA_DIR / "vapid.json",
    "HEARTBEAT_FILE": DATA_DIR / "worker-heartbeat",
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.ui",
    "apps.events",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "civic.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.ui.context_processors.civic",
            ],
        },
    },
]

WSGI_APPLICATION = "civic.wsgi.application"

# SQLite en WAL avec verrous explicites : deux processus écrivent
# (gunicorn et le worker), voir docs/adr/0004-sqlite-wal.md.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "db" / "civic.sqlite3",
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;",
            "transaction_mode": "IMMEDIATE",
        },
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = DATA_DIR / "static"
MEDIA_ROOT = DATA_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Courriel : MailHog en démo, relais réel en production (voir .env.example).
EMAIL_HOST = os.environ.get("CIVIC_SMTP_HOST", "")
EMAIL_PORT = int(os.environ.get("CIVIC_SMTP_PORT", "1025"))
EMAIL_HOST_USER = os.environ.get("CIVIC_SMTP_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("CIVIC_SMTP_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("CIVIC_SMTP_TLS", "0") == "1"
DEFAULT_FROM_EMAIL = os.environ.get("CIVIC_SMTP_FROM", f"mairie@{CIVIC_DOMAIN}")
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST
    else "django.core.mail.backends.console.EmailBackend"
)

# Derrière Caddy : le proxy termine le TLS et pose les en-têtes.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
