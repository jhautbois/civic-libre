#!/bin/sh
# Prépare la base et les fichiers au démarrage du conteneur core.
# Le worker ne passe pas par ici (entrypoint dédié dans compose.yaml)
# pour éviter deux migrations concurrentes.
set -e

python manage.py migrate --noinput
python manage.py createcachetable
python manage.py ensure_vapid
python manage.py collectstatic --noinput

if [ "${CIVIC_DEMO:-0}" = "1" ]; then
    python manage.py seed_demo
fi

exec "$@"
