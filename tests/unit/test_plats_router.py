#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_plats_router.py - Tests unitaires pour plats_router

Description:
    Tests unitaires pour src/modules/commandes_saisie/utils/plats_router.py.
    Les modules "rooting" réels important PySide6, ils sont systématiquement
    mockés via monkeypatch sur importlib.import_module : on ne teste ici que
    la logique de routage, pas l'ouverture effective des dialogues Qt.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.19

Date de modification:
    2026.06.19
"""

import pytest
from unittest.mock import MagicMock

from src.modules.commandes_saisie.utils import plats_router


@pytest.fixture
def mock_card(monkeypatch):
    """Remplace get_card_data() par une carte de test contrôlée."""
    card = {
        "Pizza": {"Prix": 8.5, "module": "pizza"},
        "Frites": {"Prix": 3.0},  # pas de champ "module" -> découverte par slug
        "Mr Freez": {"Prix": 2.0},  # slug -> "mr_freez" (module inexistant)
        "Sans Prix": {},
    }
    monkeypatch.setattr(plats_router, "get_card_data", lambda: card)
    return card


# ── _to_slug ───────────────────────────────────────────────────────────────────

class TestToSlug:
    def test_minuscule_et_espaces(self):
        assert plats_router._to_slug("Mr Freez") == "mr_freez"

    def test_supprime_accents(self):
        assert plats_router._to_slug("Salade Composée") == "salade_composee"

    def test_tirets_convertis(self):
        assert plats_router._to_slug("Pizza-Maison") == "pizza_maison"


# ── _resolve_module_path ───────────────────────────────────────────────────────

class TestResolveModulePath:
    def test_champ_module_explicite_prioritaire(self, mock_card):
        chemin = plats_router._resolve_module_path("Pizza", mock_card["Pizza"])
        assert chemin == "src.modules.plats.pizza.rooting"

    def test_decouverte_par_slug_module_existant(self, mock_card):
        # "Frites" n'a pas de champ "module", mais src/modules/plats/frites/rooting.py existe.
        chemin = plats_router._resolve_module_path("Frites", mock_card["Frites"])
        assert chemin == "src.modules.plats.frites.rooting"

    def test_aucun_module_correspondant(self, mock_card):
        chemin = plats_router._resolve_module_path("Mr Freez", mock_card["Mr Freez"])
        assert chemin is None


# ── _route_ajout_direct ────────────────────────────────────────────────────────

class TestRouteAjoutDirect:
    def test_construit_le_plat_si_prix_present(self, mock_logger):
        resultat = plats_router._route_ajout_direct("Mr Freez", {"Prix": 2.0})
        assert resultat == {
            "Plat": "Mr Freez",
            "Nom": "Mr Freez",
            "Prix": 2.0,
            "Statut": "En attente",
            "Composition": [],
        }

    def test_retourne_none_si_prix_absent(self, mock_logger):
        assert plats_router._route_ajout_direct("Sans Prix", {}) is None


# ── check_disponibilite_plat ───────────────────────────────────────────────────

class TestCheckDisponibilitePlat:
    def test_disponible_si_aucun_module_resolu(self, mock_card):
        assert plats_router.check_disponibilite_plat("Mr Freez") is True

    def test_disponible_si_module_sans_check_disponibilite(self, mock_card, monkeypatch):
        monkeypatch.setattr(plats_router.importlib, "import_module", lambda path: MagicMock(spec=[]))
        assert plats_router.check_disponibilite_plat("Pizza") is True

    def test_respecte_le_retour_du_module(self, mock_card, monkeypatch):
        module = MagicMock()
        module.check_disponibilite.return_value = False
        monkeypatch.setattr(plats_router.importlib, "import_module", lambda path: module)
        assert plats_router.check_disponibilite_plat("Pizza") is False

    def test_disponible_par_defaut_si_exception(self, mock_card, monkeypatch, mock_logger):
        monkeypatch.setattr(
            plats_router.importlib, "import_module",
            lambda path: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        assert plats_router.check_disponibilite_plat("Pizza") is True


# ── route_plat_selection ───────────────────────────────────────────────────────

class TestRoutePlatSelection:
    def test_plat_inconnu_retourne_none(self, mock_card, mock_logger):
        assert plats_router.route_plat_selection("Inexistant", None, "chemin.json") is None

    def test_delegue_au_module_resolu(self, mock_card, monkeypatch):
        module = MagicMock()
        module.route_selection.return_value = {"Plat": "Pizza", "Nom": "Margherita"}
        monkeypatch.setattr(plats_router.importlib, "import_module", lambda path: module)
        resultat = plats_router.route_plat_selection("Pizza", None, "chemin.json")
        assert resultat == {"Plat": "Pizza", "Nom": "Margherita"}
        module.route_selection.assert_called_once_with(None, "chemin.json")

    def test_retourne_none_si_exception_dans_module(self, mock_card, monkeypatch, mock_logger):
        monkeypatch.setattr(
            plats_router.importlib, "import_module",
            lambda path: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        assert plats_router.route_plat_selection("Pizza", None, "chemin.json") is None

    def test_fallback_ajout_direct_si_aucun_module(self, mock_card, mock_logger):
        resultat = plats_router.route_plat_selection("Mr Freez", None, "chemin.json")
        assert resultat["Plat"] == "Mr Freez"
        assert resultat["Prix"] == 2.0

    def test_fallback_retourne_none_si_prix_absent(self, mock_card, mock_logger):
        assert plats_router.route_plat_selection("Sans Prix", None, "chemin.json") is None
