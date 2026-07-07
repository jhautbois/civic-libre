# Civic Libre

Application citoyenne municipale libre, clé en main, pour une petite
commune française. Un habitant consulte l'agenda, reçoit les alertes
de la mairie et signale un lampadaire en panne en trois gestes ; les
agents traitent des signalements déjà triés ; tout est standard,
auto-hébergé et réversible.

Projet personnel de recherche et développement en logiciel libre, mené
à titre privé et hors de tout mandat électif. Il ne préjuge d'aucune
adoption par une collectivité. Licence AGPL-3.0.

## Essayer en cinq minutes

```bash
git clone <ce dépôt> && cd civic-libre
docker compose up -d
```

Puis https://civic.localhost (application) et
https://agenda.civic.localhost (Gancio, saisie des événements).
Certificats locaux autosignés : l'avertissement du navigateur est
normal. Comptes de démonstration : `maire`, `secretariat`,
`agent-technique` (mot de passe `demo-civic-libre`). Courriels de
démonstration : http://localhost:8025.

## Ce que fait l'application

- **Agenda communal** : saisie et modération dans
  [Gancio](https://gancio.org) (adopté tel quel), consultation dans la
  PWA, flux iCal (RFC 5545 et 7986) et RSS générés par le cœur,
  notification des nouveaux événements.
- **Annonces et alertes** : une saisie unique diffuse vers le fil,
  le flux RSS et les notifications (les alertes partent en priorité,
  en moins de dix secondes).
- **Signalements** : photo (EXIF purgé), position (carte ou adresse,
  géocodage Base Adresse Nationale), suivi public par référence,
  modération avant publication, back-office par service avec statuts,
  et une **API Open311 GeoReport v2 complète** (JSON et XML, extensions
  FixMyStreet pour les statuts détaillés).
- **Notifications Web Push** (RFC 8030/8291/8292, clés VAPID
  auto-générées, aucun compte tiers), PWA installable, hors-ligne de
  base, thème clair et sombre aux couleurs de la commune (contrastes
  dérivés automatiquement, RGAA).

## Principes

Réutiliser avant de construire : Gancio pour l'agenda, Caddy pour le
HTTPS, la Géoplateforme IGN pour les adresses, Leaflet et
OpenStreetMap pour la carte (tuiles relayées : l'adresse IP des
habitants ne sort pas). Le cœur (Django 5.2 LTS, SQLite) n'écrit que
l'écart irréductible. Pas de compte citoyen, pas de traceur, pas de
store, pas de péage par habitant. Données minimisées et anonymisation
automatique (RGPD), accessibilité travaillée dès la conception et
contrôlée en continu (axe-core), le tout documenté en français pour
être maintenable par des tiers.

## Documentation

| Document | Contenu |
|---|---|
| [docs/spec.md](docs/spec.md) | Spécification validée (périmètre, parcours, exigences) |
| [docs/etat-de-l-art.md](docs/etat-de-l-art.md) | Phase 0 sourcée : 11 candidats libres évalués, benchmark, standards |
| [docs/architecture.md](docs/architecture.md) | Conteneurs, modèle de données, API, worker |
| [docs/design.md](docs/design.md) | Système de design (tokens, composants, écriture) |
| [docs/adr/](docs/adr/) | Décisions structurantes |
| [docs/exploitation/installation.md](docs/exploitation/installation.md) | Installation production (VPS, checklist) |
| [docs/exploitation/exploitation.md](docs/exploitation/exploitation.md) | Sauvegardes, mises à jour, incidents, réversibilité |
| [docs/exploitation/guide-agent.md](docs/exploitation/guide-agent.md) | Guide de l'agent municipal |
| [docs/exploitation/guide-administrateur.md](docs/exploitation/guide-administrateur.md) | Guide de l'administrateur |
| [docs/exploitation/audit-rgaa.md](docs/exploitation/audit-rgaa.md) | Grille RGAA 4.1.2 auto-évaluée |
| [docs/exploitation/modeles/](docs/exploitation/modeles/) | Modèles RGPD et accessibilité à adapter |
| [docs/exploitation/ce-qui-manque-pour-la-production.md](docs/exploitation/ce-qui-manque-pour-la-production.md) | Note honnête avant mise en service |

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md). L'API Open311 est servie sous
`/open311/v2/` (discovery, services, requests, servicerequestupdates).
Tests : `cd backend && pytest` (et `pytest -m a11y` avec chromium).
