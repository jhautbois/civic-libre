"""Garde-fou structurel sur compose.yaml (le démarrage réel est vérifié en recette)."""

from pathlib import Path

import yaml

COMPOSE = Path(__file__).parents[2] / "compose.yaml"


def test_services_et_volumes_attendus():
    config = yaml.safe_load(COMPOSE.read_text())
    assert set(config["services"]) == {"caddy", "core", "worker", "gancio", "mailhog"}
    assert set(config["volumes"]) == {"caddy_data", "caddy_config", "core_data", "gancio_data"}


def test_worker_partage_les_donnees_du_coeur():
    config = yaml.safe_load(COMPOSE.read_text())
    assert "core_data:/data" in config["services"]["worker"]["volumes"]
    assert "core_data:/data" in config["services"]["core"]["volumes"]


def test_gancio_epingle_par_digest():
    """ADR 0003 : l'image Gancio est épinglée par digest, pas seulement par tag."""
    config = yaml.safe_load(COMPOSE.read_text())
    image = config["services"]["gancio"]["image"]
    assert "gancio" in image
    assert "@sha256:" in image
