# Architecture détaillée

Livrable de la phase 3. La spécification validée est dans docs/spec.md ; les décisions structurantes sont tracées dans docs/adr/.

## Vue d'ensemble

Quatre conteneurs orchestrés par docker compose, deux domaines :

```
                        Internet
                           │
                  [caddy]  ├── commune.fr          → core (gunicorn :8000)
                  HTTPS    ├── agenda.commune.fr   → gancio (:13120)
                  auto     └── commune.fr/tuiles/* → proxy cache tuiles

  [core]    Django 5.2 LTS : PWA citoyenne, back-office, Open311, flux, push
  [worker]  même image que core : boucles de tâches (outbox, synchro, purges)
  [gancio]  v1.28.2 épinglée : saisie et modération des événements

  Volumes : core_data (SQLite WAL + médias), gancio_data, caddy_data
  Externes : relais SMTP, data.geopf.fr (géocodage BAN), fournisseur de tuiles
```

En démonstration locale : `civic.localhost` et `agenda.civic.localhost`, TLS interne Caddy, données d'exemple chargées au premier démarrage.

## Structure du dépôt

```
civic-libre/
├── compose.yaml              # démo clé en main ; overrides documentés pour la prod
├── Caddyfile
├── .env.example              # toutes les variables, commentées en français
├── LICENSE                   # AGPL-3.0
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml        # dépendances et outillage (ruff, pytest)
│   ├── manage.py
│   ├── civic/                # paquet projet Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── events/           # miroir Gancio, vues agenda, flux ics et rss
│   │   ├── announcements/    # annonces et alertes, flux rss
│   │   ├── reports/          # signalements, modération, Open311
│   │   ├── push/             # abonnements Web Push, outbox, envoi
│   │   └── ui/               # gabarits, statiques, design system, PWA, /sante
│   └── tests/                # tests transverses (contrats, compose, santé)
└── docs/
    ├── spec.md               # spécification validée
    ├── etat-de-l-art.md      # phase 0 sourcée
    ├── architecture.md       # ce document
    ├── design.md             # système de design
    ├── adr/                  # décisions d'architecture
    ├── plans/                # plans d'implémentation par lot
    └── exploitation/         # guides installation, exploitation, agent, admin
```

Principe : chaque app Django a une responsabilité unique, ses modèles, ses vues, ses gabarits et ses tests. Identifiants en anglais, interface et documentation en français.

## Modèle de données (apps et modèles)

Noms de code en anglais, correspondance avec la spec entre parenthèses.

### apps/reports

- `Category` (Categorie) : `code` (slug stable, clé Open311), `name`, `description`, `icon`, `department` (FK), `is_active`.
- `Department` (ServiceMunicipal) : `name`, `notification_email`, `members` (M2M vers User).
- `Report` (Signalement) : `reference` (ex. R-2026-0042, unique), `category` (FK), `description` (≤ 4 000), `latitude`, `longitude`, `address`, `status` (`new`, `in_progress`, `resolved`, `rejected`), `rejection_reason`, `reporter_email` (nullable, jamais exposé), `created_ip`, `created_user_agent` (LCEN, purgés à l'anonymisation), `tracking_token`, `publication_state` (`pending`, `published`, `hidden`), `created_at`, `closed_at`, `anonymized_at`.
- `ReportPhoto` (PhotoSignalement) : `report` (FK), `image` (ré-encodée, EXIF supprimé), `thumbnail`, `moderation_state` (`pending`, `approved`, `rejected`), `alt_text` (défaut normalisé).
- `ReportUpdate` (MiseAJourSignalement) : `report` (FK), `old_status`, `new_status`, `public_comment`, `media_url` (nullable), `author` (FK User), `created_at`.

### apps/announcements

- `Announcement` (Annonce) : `title`, `body`, `level` (`info`, `alert`), `image` (nullable), `image_is_decorative` (bool), `image_alt` (requis si informative), `is_pinned`, `published_at`, `expires_at` (nullable).

### apps/events

- `MirroredEvent` (EvenementMiroir) : `gancio_id`, `title`, `starts_at`, `ends_at`, `place_name`, `place_address`, `tags` (JSON), `image_url`, `image_alt`, `url`, `synced_at`, `notified` (bool, déclenchement push unique). Fenêtre glissante : passé 1 mois, futur 6 mois.

### apps/push

- `PushSubscription` (AbonnementPush) : `endpoint` (unique), `p256dh`, `auth`, `topics` (JSON parmi `events`, `news`, `alerts`), `created_at`, `last_success_at`, `failure_count`.
- `OutgoingNotification` (NotificationSortante) : `topic`, `priority` (`alert` > `normal`), `title`, `body`, `url`, `created_at`, `state` (`pending`, `sending`, `done`), plus table de livraison `NotificationDelivery` (`notification` FK, `subscription` FK, `state`, `attempts`, unique ensemble) pour l'idempotence at-least-once sans doublon.

### Comptes

`django.contrib.auth` avec groupes `agent`, `manager`, `admin`. Le persona administrateur passe par l'admin Django (personnalisé a minima). Seule la file de traitement agents est une interface sur mesure.

## API et routes

### Citoyennes (HTML rendu serveur, français)

- `/` fil unifié (alertes, annonces épinglées, prochains événements), pagination « Voir plus ».
- `/agenda/`, `/agenda/<id>/` : liste filtrable et détail événement (tuile date, lien iCal).
- `/annonces/<id>/` : détail annonce.
- `/signaler/` : formulaire par étapes (fonctionne sans JavaScript ; la carte devient saisie d'adresse).
- `/suivi/<reference>/` : page publique de suivi (contenus publiés uniquement) ; `?jeton=` révèle au déclarant son propre contenu en attente.
- `/notifications/` : gestion de l'abonnement push (opt-in par sujets, désabonnement).
- `/infos/`, `/confidentialite/`, `/accessibilite/` : pages statiques.
- `/sante` : JSON agrégé (synchro, push, courriel, disque, âge de sauvegarde) pour la supervision.

### Flux

- `/flux/evenements.ics` : iCal RFC 5545 + 7986 (UID stables `evt-<gancio_id>@<domaine>`, TZID Europe/Paris avec VTIMEZONE, NAME, SOURCE, REFRESH-INTERVAL:P1D), fenêtre glissante.
- `/flux/evenements.rss`, `/flux/annonces.rss` : RSS 2.0, framework de syndication Django, guid permaliens stables vers la PWA.

### Open311 GeoReport v2 (JSON et XML)

Voir le tableau normatif dans docs/spec.md. Implémentation : vues Django dédiées (pas de DRF, sérialisation explicite testée par contrats), `metadata=false`, mode temps réel (POST renvoie `service_request_id`), extension `GET /open311/v2/servicerequestupdates.[format]` au format FixMyStreet exact, statuts étendus dans les updates (IN_PROGRESS, FIXED, NO_FURTHER_ACTION, NOT_COUNCILS_RESPONSIBILITY). Couche service partagée `reports/services.py` : une seule fonction de création validée, deux adaptateurs (formulaire, Open311).

### Back-office (authentifié)

- `/gestion/` : file de signalements du service de l'agent (filtres par statut), détail avec carte et photos, transition de statut avec commentaire public, modération des photos et descriptions.
- `/gestion/annonces/` : CRUD annonces (alternative d'image obligatoire à la saisie).
- `/admin/` : admin Django (catégories, services, comptes, réglages commune).
- Lien croisé visible vers l'admin Gancio (`https://agenda.<domaine>/admin`).

## Worker

Processus unique (`manage.py run_worker`), deux cadences, heartbeat fichier partagé avec `/sante` :

- Boucle courte (~10 s) : dépile `OutgoingNotification` par priorité (`alert` d'abord), envoie via pywebpush en pool borné (8 threads), TTL selon niveau (alertes 3600 s, reste 86 400 s), backoff exponentiel sur 429 et 5xx, purge des abonnements sur 404 et 410, marque les livraisons (idempotence par couple notification et abonnement).
- Boucle lente (5 min) : synchronisation Gancio (`GET /api/events` sur fenêtre glissante, création des notifications pour les nouveaux événements), anonymisation planifiée (12 mois après clôture, butoir 24 mois après création), purge des abonnements en échec depuis 6 mois, alerte courriel exploitant sur échec répété d'une tâche.

Reprise après crash : les états `sending` datés de plus de 5 minutes redeviennent `pending` ; les livraisons déjà `done` ne sont jamais renvoyées.

## Configuration (variables d'environnement)

| Variable | Rôle | Défaut démo |
|---|---|---|
| `CIVIC_DOMAIN` | domaine citoyen | `civic.localhost` |
| `CIVIC_AGENDA_DOMAIN` | domaine Gancio | `agenda.civic.localhost` |
| `CIVIC_SECRET_KEY` | clé Django (générée si absente) | générée |
| `CIVIC_COMMUNE_NAME` | nom affiché | `Villebourg` |
| `CIVIC_ACCENT_COLOR` | teinte communale (dérivée automatiquement) | `#31597F` |
| `CIVIC_GEOCODING_URL` | géocodage BAN | `https://data.geopf.fr/geocodage` |
| `CIVIC_TILES_URL` | fournisseur de tuiles (proxifié) | OSM France |
| `CIVIC_SMTP_*` | hôte, port, identifiants, expéditeur | MailHog en démo |
| `CIVIC_OPERATOR_EMAIL` | alertes exploitant | vide (désactivé) |
| `GANCIO_API_URL` | API interne Gancio | `http://gancio:13120` |

Clés VAPID : générées au premier démarrage dans le volume de données (`vapid.json`), jamais dans l'image ni le dépôt. Leur sauvegarde est critique (voir docs/exploitation/).

## SQLite

`journal_mode=WAL`, `busy_timeout=5000`, transactions `IMMEDIATE` (options Django `init_command` et `transaction_mode`), volume sur disque local. Sauvegarde uniquement par `sqlite3 .backup` ou `VACUUM INTO` (jamais de copie de fichier à chaud), pour la base du cœur ET celle de Gancio. PostgreSQL documenté en option pour les déploiements mutualisés.

## Sécurité

- Caddy : HTTPS automatique, HSTS, en-têtes de sécurité ; CSP stricte (`default-src 'self'`, pas de script externe, tuiles via le proxy même origine).
- Django : CSRF, sessions durcies, Argon2, `SECURE_*` activés derrière proxy.
- Formulaires publics et POST Open311 : limitation de débit par IP (fenêtre courte, IP non journalisée au delà du strict nécessaire), pot de miel, taille d'upload bornée (8 Mo), ré-encodage Pillow (supprime EXIF et charges utiles).
- `media_url` Open311 entrante : stockée, jamais téléchargée (SSRF), jamais publiée sans modération.
- Images docker épinglées par digest ; renovate sur le dépôt ; script de mise à jour une commande pour les instances.

## Frontend et PWA

Gabarits Django + CSS sur mesure (voir docs/design.md) + JavaScript progressif en modules natifs, sans framework ni bundler : `map.js` (Leaflet 1.9.4 auto-hébergée), `geolocate.js`, `push.js` (abonnement), `sw.js` (service worker : réception push, cache de l'app shell, hors-ligne de base), `manifest.webmanifest` généré (nom et couleurs de la commune). Tout fonctionne sans JavaScript pour la consultation et le signalement.

## Tests

- Unitaires et intégration : pytest + pytest-django (base SQLite mémoire, settings dédiés).
- Contrats Open311 : suite dédiée validant JSON et XML champ à champ contre la spec (fixtures).
- Contrats Gancio : exécutés en CI contre l'image épinglée (schéma de `/api/events`, présence des flux) ; repli documenté (parsing iCal).
- Flux : validation icalendar (bibliothèque) et structure RSS en CI ; validateurs externes en recette.
- Accessibilité : axe-core (via playwright) sur les parcours clés, dès le lot 1.
- Compose : `docker compose config` en CI ; démarrage complet et scénarios curl en recette de lot.
