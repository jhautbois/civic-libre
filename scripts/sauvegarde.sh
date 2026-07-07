#!/bin/sh
# Sauvegarde complète de l'instance Civic Libre.
# Usage : ./scripts/sauvegarde.sh [dossier-destination]   (défaut : ./sauvegardes)
#
# Méthode sûre pour SQLite (jamais de copie de fichier à chaud) :
# .backup côté cœur, VACUUM INTO côté Gancio (docs/adr/0004).
# Périmètre : bases, médias, clés (VAPID, secret), configurations.
# Chiffrement : si CIVIC_BACKUP_PASSPHRASE est défini, l'archive est
# chiffrée avec gpg (symétrique). COPIEZ LES ARCHIVES HORS DU SERVEUR.

set -eu

DEST="${1:-./sauvegardes}"
STAMP=$(date +%Y%m%d-%H%M%S)
NAME="civic-libre-$STAMP"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$DEST" "$WORK/$NAME"

echo "1/5 Base du cœur (sqlite3 .backup)"
docker compose exec -T core sqlite3 /data/db/civic.sqlite3 ".backup /data/db/sauvegarde.sqlite3"
docker compose cp core:/data/db/sauvegarde.sqlite3 "$WORK/$NAME/civic.sqlite3"
docker compose exec -T core rm /data/db/sauvegarde.sqlite3

echo "2/5 Base Gancio (VACUUM INTO)"
docker compose exec -T gancio node -e "
const sqlite3 = require('/home/node/node_modules/sqlite3');
const db = new sqlite3.Database('/home/node/data/gancio.sqlite');
db.exec(\"VACUUM INTO '/home/node/data/sauvegarde.sqlite'\", (e) => {
  if (e) { console.error(e.message); process.exit(1); }
  db.close();
});"
docker compose cp gancio:/home/node/data/sauvegarde.sqlite "$WORK/$NAME/gancio.sqlite"
docker compose exec -T gancio rm /home/node/data/sauvegarde.sqlite

echo "3/5 Médias, clés et configurations"
docker compose cp core:/data/media "$WORK/$NAME/media"
docker compose cp core:/data/vapid.json "$WORK/$NAME/vapid.json"
docker compose cp core:/data/secret_key "$WORK/$NAME/secret_key" 2>/dev/null || true
docker compose cp gancio:/home/node/data/uploads "$WORK/$NAME/gancio-uploads" 2>/dev/null || true
docker compose cp gancio:/home/node/data/config.json "$WORK/$NAME/gancio-config.json"
[ -f .env ] && cp .env "$WORK/$NAME/env" || true
cp Caddyfile "$WORK/$NAME/Caddyfile"

echo "4/5 Archive"
tar -czf "$DEST/$NAME.tar.gz" -C "$WORK" "$NAME"
if [ -n "${CIVIC_BACKUP_PASSPHRASE:-}" ]; then
    gpg --batch --yes --passphrase "$CIVIC_BACKUP_PASSPHRASE" \
        --symmetric --cipher-algo AES256 "$DEST/$NAME.tar.gz"
    rm "$DEST/$NAME.tar.gz"
    echo "   Archive chiffrée : $DEST/$NAME.tar.gz.gpg"
else
    echo "   Archive NON chiffrée : $DEST/$NAME.tar.gz"
    echo "   (définissez CIVIC_BACKUP_PASSPHRASE pour chiffrer)"
fi

echo "5/5 Rotation (90 jours) et marqueur de supervision"
find "$DEST" -name 'civic-libre-*.tar.gz*' -mtime +90 -delete
docker compose exec -T core touch /data/last-backup

echo "Terminé. Copiez l'archive HORS de ce serveur (stockage objet, second site)."
