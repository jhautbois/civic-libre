#!/bin/sh
# Restauration d'une sauvegarde Civic Libre sur une instance (neuve ou non).
# Usage : ./scripts/restauration.sh chemin/vers/civic-libre-AAAAMMJJ-HHMMSS.tar.gz
# Pour une archive chiffrée (.gpg) : la déchiffrer d'abord,
#   gpg -d archive.tar.gz.gpg > archive.tar.gz
#
# ATTENTION : remplace les données actuelles de l'instance.

set -eu

ARCHIVE="${1:?Usage : ./scripts/restauration.sh archive.tar.gz}"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

tar -xzf "$ARCHIVE" -C "$WORK"
SRC=$(find "$WORK" -maxdepth 1 -mindepth 1 -type d | head -1)

echo "1/4 Arrêt des services applicatifs"
docker compose stop core worker gancio

echo "2/4 Restauration du cœur"
docker compose cp "$SRC/civic.sqlite3" core:/data/db/civic.sqlite3
docker compose exec -T --user root core sh -c \
    'rm -f /data/db/civic.sqlite3-wal /data/db/civic.sqlite3-shm; chown -R civic:civic /data' \
    2>/dev/null || true
docker compose cp "$SRC/media" core:/data/
docker compose cp "$SRC/vapid.json" core:/data/vapid.json
[ -f "$SRC/secret_key" ] && docker compose cp "$SRC/secret_key" core:/data/secret_key

echo "3/4 Restauration de Gancio"
docker compose cp "$SRC/gancio.sqlite" gancio:/home/node/data/gancio.sqlite
[ -d "$SRC/gancio-uploads" ] && docker compose cp "$SRC/gancio-uploads" gancio:/home/node/data/uploads

echo "4/4 Redémarrage et contrôle"
docker compose start core gancio
sleep 10
docker compose start worker
DOMAIN="${CIVIC_DOMAIN:-civic.localhost}"
curl -ksf "https://$DOMAIN/sante" && echo "" && echo "Restauration terminée."
echo "Rappel : le fichier env de l'archive contient la configuration ; comparez-le à votre .env."
