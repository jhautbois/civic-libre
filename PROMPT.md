# Brief : application citoyenne municipale libre (projet personnel)

## Comment l'utiliser

Ouvre une session Claude Code en modèle Fable dans ce dossier, puis dis simplement :
« Lis PROMPT.md et exécute-le. »

Claude doit suivre la méthode ci-dessous, rester en mode plan jusqu'à la validation de la spec, et ne pas écrire de code avant mon feu vert.

## Posture

Projet personnel de recherche et développement en logiciel libre, mené à titre privé, hors de tout mandat électif. Il ne préjuge d'aucune adoption par une collectivité, décision qui, le cas échéant, suivrait un processus neutre dont l'auteur serait tenu à l'écart. Le livrable doit donc être propre, documenté, packagé et maintenable par des tiers, jamais verrouillé sur son auteur.

## Objectif

Une application citoyenne municipale libre, clé en main, pour une petite commune française d'environ 7 000 habitants sans service informatique dédié, atteinte avec le MAXIMUM DE RÉUTILISATION de l'existant. Priorités, dans cet esprit : efficacité (arriver vite au fonctionnel, très peu de code sur mesure), ergonomie et design (mobile d'abord, moderne, sobre, accessible), richesse fonctionnelle utile.

## Besoin fonctionnel

1. Donner les événements aux citoyens : un agenda communal consultable, avec notifications.
2. Permettre de signaler des problèmes (voirie, éclairage, dépôts sauvages) avec photo, géolocalisation et catégorie.
3. Ne pas surcharger les agents : une saisie unique diffusée sur plusieurs canaux, des signalements triés, routés vers le bon service, avec des statuts (à traiter, en cours, résolu).

## Règle d'or : réutiliser avant de construire

Choisir la solution dans cet ordre de préférence :
1. Adopter et configurer une solution libre existante telle quelle.
2. L'étendre ou la forker proprement.
3. Assembler des briques libres existantes avec un minimum de colle standard.
4. N'écrire du neuf que pour l'écart irréductible, en restant standard et documenté.

Formats et standards imposés : iCal pour l'agenda, RSS pour la diffusion, le standard Open311 pour le signalement, Web Push et VAPID pour les notifications. Objectif : qu'une commune puisse déployer sans dépendre d'un éditeur ni d'un développeur unique.

## Exigences non fonctionnelles

- Licence : logiciel libre à copyleft fort, AGPL-3.0 par défaut, à confirmer en phase 0 (c'est la norme du secteur, Decidim, CONSUL, Vaultwarden, DirectMairie).
- Souveraineté et RGPD : auto-hébergeable en France ou en Union européenne, hors juridiction extraterritoriale, données minimisées, base légale claire.
- Accessibilité : viser le RGAA (contraste, navigation clavier, ARIA), obligation pour une collectivité.
- Clé en main : `docker compose up` doit suffire à lancer une instance de démonstration. Faible maintenance.
- Langue française pour l'interface et les contenus.
- Tests automatisés, code lisible, documentation d'installation et de contribution.
- Design et ergonomie soignés : mobile d'abord, application web installable en PWA, interface moderne et sobre. Mobiliser le skill de design frontend.

## Méthode imposée

Utilise les skills superpowers à chaque étape (brainstorming, writing-plans, test-driven-development, requesting-code-review, verification-before-completion) et le skill de design frontend pour l'interface. Procède par phases.

GATE OBLIGATOIRE, à respecter avant tout. À la fin de la phase 2, tu t'ARRÊTES et tu attends ma validation écrite et explicite avant toute implémentation. Ce point d'arrêt prime sur tout le reste, y compris sur l'orchestration automatique de workflows ou de sous-agents : aucun agent, aucun workflow ne doit écrire de code, créer une structure de projet ou lancer un développement tant que je n'ai pas validé la spec par écrit. Tu peux mobiliser des agents en parallèle pour la recherche (phase 0) et pour les revues adverses (phases 2 et 5), mais jamais pour coder avant mon feu vert. En cas de doute, tu demandes plutôt que d'avancer.

Phase 0, choix de la base existante (état de l'art sourcé par recherche web). Évaluer et RECOMMANDER la meilleure base libre à réutiliser ou étendre, plutôt que de partir de zéro. Candidats à examiner sérieusement :
- Communecter (réseau territorial libre tout-en-un, information, agenda, associations), la piste la plus proche d'un produit intégré.
- DirectMairie et l'écosystème ADULLACT, plus le standard Open311 et ses implémentations (FixMyStreet, Mark-a-Spot), pour le signalement.
- Decidim et CONSUL pour la participation, si pertinent.
- Solutions d'agenda libre et l'API OpenAgenda, briques de notification libres (ntfy, Web Push).
Observer les solutions propriétaires de référence (Mon Village d'Ouest-France, CityAll de Lumiplan, PanneauPocket, IntraMuros, Illiwap) pour cadrer la parité fonctionnelle et surtout le niveau d'ergonomie et de design à égaler, sans rien copier. Conclusion attendue : quelle base on reprend, ce qu'on étend, ce qu'on assemble, ce qu'on écrit vraiment, et pourquoi. Recommander la licence.

Phase 1, spécification (mode plan). Périmètre du produit minimum viable, personas (habitant, agent, administrateur), parcours, modèle de données, interfaces et formats standards (iCal, RSS, Open311), architecture cible privilégiant l'extension de la base retenue, intentions d'ergonomie et de design, exigences RGPD et RGAA, stratégie de maintenance par des tiers. Rédiger une spec claire et un plan d'implémentation incrémental.

Phase 2, revue adverse de la spec. Jouer l'avocat du diable contre sa propre spec : réinvention inutile de briques existantes, sur-ingénierie, dépendances fragiles, dette de maintenance, angles morts RGPD et accessibilité. Corriger la spec. Puis STOP : présente-moi la spec finale et attends ma validation écrite. Ne passe ni en phase 3 ni en implémentation sans ce feu vert explicite, même si l'orchestration te pousse à enchaîner.

Phase 3, architecture détaillée et système de design. Structure du dépôt, dépendances, conteneurs, schémas de données et d'API, plus une base de design (palette, typographie, composants accessibles).

Phase 4, implémentation incrémentale en TDD. Petits lots testés, du plus petit produit démontrable vers le complet, priorité à l'agenda et au signalement, avec une interface soignée.

Phase 5, revue interne de l'implémentation. Revue de code contre la spec et contre les standards (Open311, iCal, RGPD, RGAA, sécurité), correction des écarts, vérification effective que l'application tourne, pas seulement que les tests passent.

Phase 6, packaging clé en main. docker compose de démonstration, README, guide d'installation et de déploiement, fichier de licence, guide de contribution destiné à d'éventuels mainteneurs tiers, et une note honnête sur ce qui manque pour un usage en production.

## Livrables

Un dépôt structuré avec README, LICENSE, une spec, une architecture, un document de design, un prototype fonctionnel démontrable via docker compose, les tests, et les guides d'installation et de contribution.

## Conventions

Français, accents corrects, pas de tiret comme ponctuation (virgules, deux-points, points). Commits clairs. Sourcer les affirmations d'état de l'art. Signaler honnêtement les incertitudes et les limites plutôt que de les masquer.

## Démarrage

Commence par la phase 0, le choix de la base existante, puis enchaîne sur la spec en mode plan. Ne code pas, ne crée pas la structure du projet, ne lance aucun développement avant ma validation écrite de la spec, même si l'orchestration automatique te pousse à avancer.
