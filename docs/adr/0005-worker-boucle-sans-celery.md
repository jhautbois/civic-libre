# ADR 0005 : worker en boucle Python avec outbox, ni Celery ni Redis

Date : 2026-07-07. Statut : accepté (contrat durci en phase 2).

## Contexte
Les envois push, la synchronisation Gancio et les purges exigent des tâches de fond. Celery et
Redis ajouteraient deux services à opérer pour une commune sans informaticien.

## Décision
Un processus worker unique (manage.py run_worker), deux cadences : boucle courte (~10 s) qui
dépile une outbox priorisée (alertes d'abord) avec pool borné, backoff sur 429/5xx, purge des
abonnements 404/410 ; boucle lente (5 min) pour la synchro Gancio, l'anonymisation et les alertes
exploitant. Idempotence par table de livraison (couple notification et abonnement unique).
Heartbeat fichier exposé par /sante. Reprise : les envois en cours depuis plus de 5 minutes
redeviennent à traiter ; les livraisons faites ne sont jamais rejouées.

## Conséquences
Sémantique at-least-once sans doublon, zéro service supplémentaire. Une alerte part en moins de
10 secondes même pendant une synchronisation.
