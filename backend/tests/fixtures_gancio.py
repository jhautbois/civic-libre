"""Charge utile représentative de GET /api/events de Gancio v1.28."""

GANCIO_EVENTS = [
    {
        "id": 42,
        "title": "Fête de la musique",
        "slug": "fete-de-la-musique",
        "description": "<p>Concerts gratuits dans le centre-bourg.</p>",
        "multidate": False,
        "start_datetime": 1784397600,
        "end_datetime": 1784412000,
        "tags": ["musique", "famille"],
        "place": {"id": 1, "name": "Place de la Mairie", "address": "1 place de la Mairie"},
        "media": [{"url": "abcd1234.jpg", "name": "Affiche de la fête de la musique"}],
    },
    {
        "id": 43,
        "title": "Conseil municipal",
        "slug": "conseil-municipal-juillet",
        "description": "",
        "multidate": False,
        "start_datetime": 1784484000,
        "end_datetime": None,
        "tags": [],
        "place": {"id": 2, "name": "Salle du conseil", "address": ""},
        "media": [],
    },
    {
        # Événement invalide : sans titre, doit être ignoré sans casser la synchro.
        "id": 44,
        "title": "",
        "start_datetime": 1784484000,
    },
]
