# ADR 0004 : SQLite en WAL par défaut, PostgreSQL en option

Date : 2026-07-07. Statut : accepté.

## Contexte
Volumétrie d'une commune de 7 000 habitants très en deçà des limites de SQLite. Deux processus
écrivains (gunicorn, worker). L'exploitation par des tiers non spécialistes est le critère dominant.

## Décision
SQLite avec journal_mode=WAL, busy_timeout=5000, transactions IMMEDIATE (options Django 5.1+),
volume disque local uniquement. Sauvegarde exclusivement par sqlite3 .backup ou VACUUM INTO
(bases du cœur ET de Gancio). PostgreSQL documenté pour les déploiements mutualisés.

## Conséquences
Un service de moins à opérer et sauvegarder trivialement, au prix d'une vigilance sur la
concurrence d'écriture (couverte par un test dédié au lot 6).
