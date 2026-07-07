"""Registres des tâches du worker.

Chaque application ajoute ses tâches ici, explicitement, pour que la
liste complète reste lisible d'un coup d'œil (voir docs/adr/0005).
Une tâche est un simple appelable sans argument ; le worker isole les
exceptions et journalise.
"""

SHORT_TASKS: list = [
    # Lot 6 : envoi de l'outbox de notifications, purge 404/410.
]

LONG_TASKS: list = [
    # Lot 1 : synchronisation Gancio.
    # Lot 4 : anonymisation planifiée des signalements.
]
