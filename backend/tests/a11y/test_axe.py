"""Filet anti-régression accessibilité : axe-core sur les parcours clés.

Ce n'est PAS un audit RGAA (voir docs/spec.md, cadrage juridique) :
axe-core détecte une partie des non-conformités automatisables. La
grille RGAA auto-évaluée du lot 7 fait référence.

Marqueur ``a11y`` : job CI dédié (navigateur chromium requis).
"""

import datetime
import json
import os
from pathlib import Path

import pytest
from django.utils import timezone

# L'API synchrone de playwright coexiste avec la boucle d'événements du
# serveur de test ; aucune requête ORM concurrente n'a lieu ici.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

from apps.events.models import MirroredEvent

AXE_JS = (Path(__file__).parent / "axe.min.js").read_text()

PAGES = ["/", "/agenda/"]

playwright_sync = pytest.importorskip(
    "playwright.sync_api", reason="playwright absent : job a11y uniquement"
)

pytestmark = [pytest.mark.a11y, pytest.mark.django_db(transaction=True)]


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:  # noqa: BLE001
            pytest.skip("chromium non installé (playwright install chromium)")
        yield browser
        browser.close()


@pytest.fixture()
def demo_data():
    MirroredEvent.objects.create(
        gancio_id=1,
        title="Fête de la musique",
        starts_at=timezone.now() + datetime.timedelta(days=7),
        place_name="Place de la Mairie",
    )


@pytest.mark.parametrize("path", PAGES)
def test_axe_sans_violation_grave(browser, live_server, demo_data, path):
    page = browser.new_page()
    page.goto(live_server.url + path)
    page.evaluate(AXE_JS)
    results = page.evaluate(
        "async () => await axe.run(document, {runOnly:{type:'tag',"
        "values:['wcag2a','wcag2aa','wcag21aa']}})"
    )
    page.close()

    graves = [v for v in results["violations"] if v.get("impact") in ("serious", "critical")]
    details = json.dumps(
        [{"id": v["id"], "impact": v["impact"], "nodes": len(v["nodes"])} for v in graves],
        ensure_ascii=False,
        indent=2,
    )
    assert not graves, f"Violations axe-core sur {path} :\n{details}"
