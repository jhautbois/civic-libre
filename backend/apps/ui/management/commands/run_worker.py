"""Worker de tâches de fond : deux cadences, un heartbeat, zéro dépendance.

Voir docs/adr/0005-worker-boucle-sans-celery.md. La boucle courte
(SHORT_INTERVAL) dépile les envois urgents ; la boucle longue
(LONG_INTERVAL) porte les synchronisations et purges. Chaque tâche est
isolée : une panne est journalisée, jamais propagée.
"""

import logging
import signal
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.ui import tasks

logger = logging.getLogger(__name__)

SHORT_INTERVAL = 10
LONG_INTERVAL = 300


class Command(BaseCommand):
    help = "Lance le worker de tâches de fond (boucles courte et longue)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Exécute une seule itération des deux boucles puis s'arrête (tests, cron).",
        )

    def handle(self, *args, **options):
        self._running = True
        signal.signal(signal.SIGTERM, self._stop)
        last_long_run = 0.0

        while True:
            self._run_all(tasks.SHORT_TASKS)
            now = time.monotonic()
            if options["once"] or now - last_long_run >= LONG_INTERVAL:
                self._run_all(tasks.LONG_TASKS)
                last_long_run = now
            self._beat()
            if options["once"] or not self._running:
                break
            time.sleep(SHORT_INTERVAL)

    def _stop(self, signum, frame):
        logger.info("Arrêt du worker demandé (SIGTERM)")
        self._running = False

    def _run_all(self, registry):
        for task in registry:
            try:
                task()
            except Exception:
                logger.exception("Tâche en échec : %s", getattr(task, "__name__", task))

    def _beat(self):
        heartbeat = settings.CIVIC["HEARTBEAT_FILE"]
        heartbeat.parent.mkdir(parents=True, exist_ok=True)
        heartbeat.touch()
