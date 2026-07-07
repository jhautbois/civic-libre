# ADR 0003 : Gancio v1.28.2 épinglée par digest, migration v2 planifiée

Date : 2026-07-07. Statut : accepté.

## Contexte
v1.28.2 (14/12/2025) est la dernière release stable de la branche 1.x (vérifié sur l'API Framagit
le 07/07/2026, contre un constat erroné de la revue adverse). La branche 2.x est en alpha/bêta ;
l'amont traite la migration v1 vers v2 comme une réinstallation. Facteur bus proche de 1.

## Décision
Épingler cisti/gancio v1.28.2 par digest. Tests de contrat en CI sur la surface consommée
(GET /api/events, flux). Migration vers la v2 planifiée à sa première stable, tracée au guide
d'exploitation. Repli si rupture : synchronisation par parsing du flux iCal seul, puis module
événements interne minimal en dernier recours.

## Conséquences
Pas de bêta en production. La dette de migration est explicite et surveillée, pas subie.
