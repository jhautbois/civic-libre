# Contribuer à Civic Libre

Merci de votre intérêt. Ce projet est pensé pour être maintenable par
des tiers : les décisions structurantes sont tracées (docs/adr/), la
spécification fait foi (docs/spec.md), et tout changement passe par
les tests.

## Mise en place

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e . --group dev
.venv/bin/pytest                 # tests unitaires et d'intégration
.venv/bin/pytest -m a11y         # contrôles axe-core (playwright install chromium)
.venv/bin/ruff check . && .venv/bin/ruff format .
```

Pile complète : `docker compose up -d` à la racine (voir README).
Lancer le cœur seul en développement :
`CIVIC_DEBUG=1 .venv/bin/python manage.py runserver`.

## Règles

- **Langues** : identifiants et code en anglais ; interface,
  documentation et messages de commit en français.
- **Tests exigés** pour toute contribution ; axe-core doit rester
  vert sur les pages publiques ; les endpoints Open311 sont couverts
  par des tests de contrat champ à champ, ne les affaiblissez pas.
- **Accessibilité et RGPD par conception** : pas de style inline
  (la CSP les bloque), alternatives obligatoires aux images
  informatives, pas de nouvelle collecte de données sans mise à jour
  de docs/exploitation/modeles/registre-traitements.md et de la page
  confidentialité.
- **Sobriété** : pas de nouvelle dépendance ni de nouveau service
  sans ADR ; le compose de démonstration doit rester à cinq services.
- **Messages de commit** : `sous-système: Résumé` (50 caractères),
  corps à 72, terminé par `Signed-off-by`.

## Où intervenir

| Sujet | Emplacement |
|---|---|
| Agenda (miroir Gancio, flux) | backend/apps/events/ |
| Annonces | backend/apps/announcements/ |
| Signalements, Open311 | backend/apps/reports/ |
| Notifications push | backend/apps/push/ |
| PWA, design, santé, worker | backend/apps/ui/ |

## Signaler un problème de sécurité

Ne pas ouvrir de ticket public : écrire au mainteneur (voir dépôt)
avec les détails ; un correctif sera publié avant divulgation.
