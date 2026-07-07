#!/bin/sh
# Mise à jour de l'instance en une commande, avec filet de sécurité.
# Usage : ./scripts/mise-a-jour.sh
# Retour arrière : git log --oneline pour retrouver la version
# précédente, puis git checkout <version> && docker compose up -d --build,
# et si besoin ./scripts/restauration.sh sur la sauvegarde faite ici.

set -eu

echo "1/4 Sauvegarde préalable"
./scripts/sauvegarde.sh

echo "2/4 Récupération de la nouvelle version"
git pull --ff-only

echo "3/4 Reconstruction et redémarrage"
docker compose build
docker compose up -d

echo "4/4 Contrôle de santé"
sleep 15
DOMAIN="${CIVIC_DOMAIN:-civic.localhost}"
curl -ksf "https://$DOMAIN/sante" && echo "" && echo "Mise à jour terminée."
