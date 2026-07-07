# Lot 0 : fondations, plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docker compose up` sert une page d'accueil sur `civic.localhost` et Gancio sur `agenda.civic.localhost`, avec CI, worker à heartbeat et clés VAPID auto-générées.

**Architecture:** voir docs/architecture.md. Quatre conteneurs (caddy, core, worker, gancio) plus MailHog en démo. Django 5.2 LTS, SQLite WAL, aucun framework JS.

**Tech Stack:** Python ≥ 3.12, Django 5.2, gunicorn, whitenoise, pywebpush (py-vapid), Pillow, requests, argon2-cffi ; pytest + pytest-django, ruff ; Caddy 2, Gancio 1.28.2, MailHog.

Convention : chaque tâche suit le cycle TDD (test écrit, test rouge, implémentation minimale, test vert, commit via /smart-commit). Les commandes se lancent depuis `backend/` dans le venv `.venv`.

---

### Task 1 : squelette Python et Django

**Files:** Create: `backend/pyproject.toml`, `backend/manage.py`, `backend/civic/{__init__,settings,urls,wsgi}.py`, `backend/apps/__init__.py`, `backend/apps/ui/` (app vide), `backend/tests/test_settings.py`, `.gitignore`.

- [x] Test : `tests/test_settings.py` vérifie `LANGUAGE_CODE == "fr"`, `TIME_ZONE == "Europe/Paris"`, hasher Argon2 en tête, options SQLite (`init_command` contient `busy_timeout` et `journal_mode=WAL`, `transaction_mode == "IMMEDIATE"`).
- [x] Rouge : `pytest tests/test_settings.py` échoue (module civic absent).
- [x] Implémentation : settings pilotés par variables `CIVIC_*` (SECRET_KEY générée en dev, DEBUG, domaine, data dir `.data` par défaut), SQLite `OPTIONS={"init_command": "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;", "transaction_mode": "IMMEDIATE"}`, whitenoise, `LANGUAGE_CODE="fr"`, `TIME_ZONE="Europe/Paris"`, `USE_TZ=True`.
- [x] Vert, puis commit `core: Squelette Django et configuration SQLite WAL`.

### Task 2 : app ui, page d'accueil, /sante

**Files:** Create: `backend/apps/ui/{views,urls,health}.py`, `backend/apps/ui/templates/ui/{base,home}.html`, `backend/tests/test_ui.py`.

- [x] Tests : `GET /` → 200, contient le nom de la commune (`CIVIC_COMMUNE_NAME`), lang="fr", landmarks (`<main>`, `<nav>` absente au lot 0, titre h1). `GET /sante` → 200 JSON avec `db: "ok"`, `disk_free_mb` entier, `worker_heartbeat_age_s` nullable.
- [x] Rouge, implémentation (vue santé : `SELECT 1`, `shutil.disk_usage`, mtime du fichier heartbeat `$DATA/worker-heartbeat`), vert, commit `ui: Accueil minimal et endpoint de santé`.

### Task 3 : worker à heartbeat

**Files:** Create: `backend/apps/ui/management/commands/run_worker.py`, `backend/tests/test_worker.py`.

- [x] Test : `call_command("run_worker", once=True)` écrit le fichier heartbeat et exécute les registres `SHORT_TASKS`/`LONG_TASKS` (vides mais appelés, monkeypatch sentinelle).
- [x] Implémentation : boucle courte (10 s) et longue (300 s), `--once` pour une itération, arrêt propre sur SIGTERM, chaque tâche isolée par try/except avec journalisation, heartbeat écrit à chaque tour court.
- [x] Vert, commit `worker: Boucle de tâches à deux cadences avec heartbeat`.

### Task 4 : clés VAPID auto-générées

**Files:** Create: `backend/apps/ui/management/commands/ensure_vapid.py`, `backend/tests/test_vapid.py`.

- [x] Test : la commande crée `$DATA/vapid.json` (clés publique et privée non vides, `sub` mailto), et ne réécrit PAS un fichier existant (idempotence vérifiée par hash).
- [x] Implémentation avec `py_vapid.Vapid` (dépendance de pywebpush), fichier en 0600.
- [x] Vert, commit `push: Génération automatique des clés VAPID`.

### Task 5 : conteneurs et compose

**Files:** Create: `backend/Dockerfile`, `backend/entrypoint.sh`, `compose.yaml`, `Caddyfile`, `gancio/config.json`, `.env.example`.

- [x] Test (CI-compatible) : `docker compose config -q` valide ; `tests/test_compose.py` vérifie que compose.yaml référence les 5 services et les volumes attendus (parse yaml).
- [x] Implémentation : image `python:3.13-slim` (multi-stage léger), entrypoint : migrate, ensure_vapid, collectstatic, gunicorn ; worker : même image, commande run_worker ; gancio `cisti/gancio:1.28.2` avec config montée (baseurl `https://agenda.civic.localhost`) ; caddy `caddy:2` avec Caddyfile (deux domaines, en-têtes de sécurité, TLS interne pour .localhost) ; mailhog pour la démo SMTP.
- [x] Vérification réelle : `docker compose up -d` puis `curl -k https://civic.localhost` (200, page accueil) et `curl -k https://agenda.civic.localhost` (200, Gancio) et `curl -k https://civic.localhost/sante` (JSON ok). 
- [x] Commit `infra: docker compose clé en main (caddy, core, worker, gancio)`.

### Task 6 : CI et pre-commit

**Files:** Create: `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, config ruff dans `pyproject.toml`.

- [x] CI : jobs lint (ruff check + format --check) et tests (pytest) sur push/PR, python 3.12 et 3.13 ; `docker compose config -q`.
- [x] pre-commit : ruff, ruff-format, fin de fichier, espaces.
- [x] Vert local (`ruff check backend`, `pytest`), commit `ci: Lint ruff et tests pytest`.

## Critère de fin de lot

`docker compose up` : accueil sur civic.localhost, Gancio sur agenda.civic.localhost, `/sante` répond, worker heartbeat visible dans `/sante`, tests et lint verts. Revue de code du lot, puis lot 1.
