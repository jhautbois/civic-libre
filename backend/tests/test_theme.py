import pytest

from apps.ui.theme import contrast, derive

# Teintes municipales difficiles : jaunes, rouges vifs, bleus clairs.
TEINTES = ["#31597F", "#FFD700", "#E30613", "#7FB3D5", "#00FF00", "#000000", "#FFFFFF"]


@pytest.mark.parametrize("accent", TEINTES)
def test_derivation_tient_les_ratios(accent):
    tokens = derive(accent)
    # Texte accentué : 4,5:1 sur papier et carte (RGAA 3.2)
    assert contrast(tokens["accent_ink"], "#F7F6F2") >= 4.5
    assert contrast(tokens["accent_ink"], "#FFFFFF") >= 4.5
    # Bouton : composant à 3:1 contre le papier (RGAA 3.3),
    # texte du bouton à 4,5:1 sur le fond du bouton (RGAA 3.2)
    assert contrast(tokens["accent"], "#F7F6F2") >= 3.0
    assert contrast(tokens["accent_text"], tokens["accent"]) >= 4.5
    # Thème sombre : texte accentué lisible sur les fonds sombres
    assert contrast(tokens["dark_accent_ink"], "#15171B") >= 4.5
    assert contrast(tokens["dark_accent_ink"], "#1E2126") >= 4.5


def test_feuille_theme(client, db):
    response = client.get("/theme.css")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/css")
    assert "--accent-ink:" in response.content.decode()
