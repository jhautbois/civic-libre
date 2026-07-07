# ADR 0002 : flux iCal et RSS des événements générés par le cœur, pas proxifiés depuis Gancio

Date : 2026-07-07. Statut : accepté (issue de la revue adverse, phase 2).

## Contexte
Le plan initial proxifiait /feed/ics et /feed/rss de Gancio sous /flux/*. La revue adverse a
montré : URL absolues pointant vers le sous-domaine Gancio (les abonnés quitteraient la PWA),
avertissement self-link au validateur W3C, export ICS Gancio en UTC sans propriétés RFC 7986,
pubDate re-notifiant à chaque édition.

## Décision
Le cœur génère /flux/evenements.ics (UID stables evt-<id>@<domaine>, TZID Europe/Paris avec
VTIMEZONE, NAME, SOURCE, REFRESH-INTERVAL) et /flux/evenements.rss (guid permaliens PWA) depuis
MirroredEvent, sur fenêtre glissante (passé 1 mois, futur 6 mois). Les exports natifs Gancio
restent disponibles sur son sous-domaine comme repli documenté.

## Conséquences
Un peu plus de code (générateurs testés en CI), en échange de la maîtrise complète de la
conformité, des liens et de la stabilité des flux publiés.
