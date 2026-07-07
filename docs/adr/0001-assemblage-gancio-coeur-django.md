# ADR 0001 : assemblage Gancio + cœur Django plutôt qu'extension d'une base existante

Date : 2026-07-07. Statut : accepté (spec validée).

## Contexte
Onze candidats libres évalués et vérifiés en phase 0 (docs/etat-de-l-art.md). Aucun ne couvre
ensemble agenda iCal/RSS, signalement Open311, Web Push et back-office simple. La règle d'or du
projet impose de réutiliser avant de construire.

## Décision
Adopter Gancio tel quel pour l'agenda (saisie, modération, récurrences). Écrire un cœur Django
5.2 LTS borné : PWA citoyenne, serveur Open311 avec extensions FixMyStreet, annonces, Web Push,
back-office signalements. Assembler par docker compose (Caddy, cœur, worker, Gancio).

## Alternatives rejetées
- Mark-a-Spot (plan B sérieux) : serveur Open311 complet mais deux écosystèmes à opérer
  (Drupal 11 + Nuxt), GPL-2.0+ sans clause réseau, quasi mono-mainteneur open core, hors politique
  de sécurité drupal.org, agenda et push à écrire en modules Drupal de toute façon.
- FixMyStreet : référence signalement mais Perl rare en France, traduction figée, ni agenda ni push.
- DirectMairie : gel fonctionnel depuis 2023, instance ADULLACT hors ligne, pas d'Open311.
- Communecter, Decidim, CONSUL, Publik, CitéLibre/Lutece, uReport : voir docs/etat-de-l-art.md.

## Conséquences
Le cœur (estimé 5 000 à 15 000 lignes tests compris) est l'écart irréductible. Il reste petit,
dans une pile généraliste, testé et documenté en français pour la reprise par des tiers.
