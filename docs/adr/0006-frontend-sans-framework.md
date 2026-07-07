# ADR 0006 : frontend rendu serveur, JavaScript progressif, Leaflet 1.9.4 épinglée

Date : 2026-07-07. Statut : accepté.

## Contexte
PWA mobile d'abord, RGAA, maintenance par des tiers, CSP stricte sans ressource externe.

## Décision
Gabarits Django + CSS sur mesure (docs/design.md) + modules JavaScript natifs sans framework ni
bundler (carte, géolocalisation, abonnement push, service worker). Consultation et signalement
fonctionnent sans JavaScript (la carte devient une saisie d'adresse). Leaflet 1.9.4 auto-hébergée
et épinglée : branche 1.x en maintenance, migration 2.x (ESM) tracée comme dette connue.

## Conséquences
Aucune chaîne de build frontend à maintenir. L'accessibilité repose sur du HTML sémantique
testable. La dette Leaflet 2.x est documentée plutôt que subie.
