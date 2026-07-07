# Journal des versions

Le format suit les versions sémantiques. Les changements de sécurité
sont signalés en tête d'entrée.

## 0.1.0 (2026-07-07)

Première version démontrable, issue de la spécification validée
(docs/spec.md) :

- Agenda communal : Gancio adopté tel quel (saisie, modération),
  miroir local, flux iCal (RFC 5545 et 7986) et RSS générés par le
  cœur, notification des nouveaux événements.
- Annonces et alertes multicanal (fil, RSS, push prioritaire).
- Signalements : formulaire accessible (avec et sans JavaScript),
  photos ré-encodées sans EXIF, géocodage BAN (Géoplateforme IGN),
  suivi public par référence, modération avant publication,
  back-office par service, anonymisation automatique (RGPD, LCEN).
- API Open311 GeoReport v2 complète (JSON et XML) avec extensions
  FixMyStreet (servicerequestupdates, statuts étendus).
- Notifications Web Push VAPID sans service tiers, PWA installable,
  hors-ligne de base, tuiles cartographiques relayées.
- Design system (fontes OFL auto-hébergées, thème sombre, dérivation
  automatique des contrastes), grille RGAA 4.1.2 auto-évaluée.
- Packaging : docker compose cinq services, scripts de sauvegarde,
  restauration et mise à jour, supervision /sante avec alertes
  exploitant, guides français complets, modèles RGPD et accessibilité.
