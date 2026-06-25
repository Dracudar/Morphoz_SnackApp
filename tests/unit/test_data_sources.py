#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_data_sources.py - Tests unitaires pour data_sources

Description:
    Tests unitaires pour src/backend/data_sources.py.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.12

Date de modification:
    2026.06.14
"""

import json
import pytest
from pathlib import Path

from src.backend import data_sources
from src.backend.data_sources import (
    _normalize_text,
    _normalized_state,
    _parse_order_file,
    get_menu_categories,
    invalider_cache_stock,
)


# ── _normalize_text ───────────────────────────────────────────────────────────

class TestNormalizeText:
    def test_minuscules(self):
        assert _normalize_text("Pizza") == "pizza"

    def test_supprime_accents(self):
        assert _normalize_text("crêpe") == "crepe"

    def test_supprime_espaces(self):
        assert _normalize_text("salade composée") == "saladecomposee"

    def test_supprime_ponctuation(self):
        assert _normalize_text("plat-du-jour") == "platdujour"

    def test_chaine_vide(self):
        assert _normalize_text("") == ""

    def test_caracteres_speciaux(self):
        assert _normalize_text("Hors-Stock!") == "horsstock"


# ── _normalized_state ─────────────────────────────────────────────────────────

class TestNormalizedState:
    def test_disponible(self):
        assert _normalized_state("Disponible") == "disponible"

    def test_avec_accents(self):
        assert _normalized_state("Retiré") == "retire"

    def test_espaces_en_bords(self):
        assert _normalized_state("  Disponible  ") == "disponible"


# ── get_menu_categories ───────────────────────────────────────────────────────

class TestGetMenuCategories:
    def _patch_card(self, monkeypatch, card_data):
        monkeypatch.setattr("src.backend.data_sources.get_card_data", lambda: card_data)
        monkeypatch.setattr("src.backend.data_sources._resolve_category_icon", lambda *a: None)

    def test_retourne_liste_vide_si_carte_vide(self, monkeypatch):
        self._patch_card(monkeypatch, {})
        assert get_menu_categories() == []

    def test_nombre_categories(self, monkeypatch):
        self._patch_card(monkeypatch, {
            "Pizza": {"Etat": "Disponible", "Recettes": {"Margherita": {}}},
            "Grillade": {"Etat": "Disponible"},
        })
        cats = get_menu_categories()
        assert len(cats) == 2

    def test_categorie_disponible(self, monkeypatch):
        self._patch_card(monkeypatch, {
            "Pizza": {"Etat": "Disponible", "Recettes": {"A": {}, "B": {}}, "Prix": 8.5},
        })
        cats = get_menu_categories()
        cat = cats[0]
        assert cat["name"] == "Pizza"
        assert cat["enabled"] is True
        assert cat["hidden"] is False
        assert cat["out_of_stock"] is False
        assert cat["recipe_count"] == 2
        assert cat["price"] == 8.5

    def test_categorie_retiree_masquee(self, monkeypatch):
        self._patch_card(monkeypatch, {"Pizza": {"Etat": "Retiré"}})
        cat = get_menu_categories()[0]
        assert cat["hidden"] is True
        assert cat["enabled"] is False

    def test_categorie_archivee_masquee(self, monkeypatch):
        self._patch_card(monkeypatch, {"Pizza": {"Etat": "Archive"}})
        cat = get_menu_categories()[0]
        assert cat["hidden"] is True

    def test_categorie_rupture_stock(self, monkeypatch):
        self._patch_card(monkeypatch, {"Pizza": {"Etat": "Rupture"}})
        cat = get_menu_categories()[0]
        assert cat["out_of_stock"] is True
        assert cat["enabled"] is False

    def test_categorie_sans_etat_est_disponible(self, monkeypatch):
        self._patch_card(monkeypatch, {"Pizza": {}})
        cat = get_menu_categories()[0]
        assert cat["enabled"] is True

    def test_has_recipes_faux_sans_recettes(self, monkeypatch):
        self._patch_card(monkeypatch, {"Pizza": {"Recettes": {}}})
        cat = get_menu_categories()[0]
        assert cat["has_recipes"] is False
        assert cat["recipe_count"] == 0


# ── invalider_cache_stock ─────────────────────────────────────────────────────

class TestInvaliderCacheStock:
    def setup_method(self):
        data_sources._stock_cache_instance = None

    def teardown_method(self):
        data_sources._stock_cache_instance = None

    def test_remet_le_singleton_a_none(self):
        data_sources._stock_cache_instance = object()
        invalider_cache_stock()
        assert data_sources._stock_cache_instance is None

    def test_sans_effet_si_deja_none(self):
        invalider_cache_stock()
        assert data_sources._stock_cache_instance is None

    def test_double_invalidation_ne_plante_pas(self):
        data_sources._stock_cache_instance = object()
        invalider_cache_stock()
        invalider_cache_stock()
        assert data_sources._stock_cache_instance is None


# ── _parse_order_file ─────────────────────────────────────────────────────────

class TestParseOrderFile:
    def _write_order(self, path, data):
        p = Path(path)
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_retourne_infos_et_commande(self, tmp_path):
        data = {
            "Informations": {"ID": "20260101-001", "Statut": "En cours"},
            "Commande": {"P001": {"Plat": "Pizza", "Statut": "En attente"}},
        }
        f = self._write_order(tmp_path / "commande_test.json", data)
        infos, commande = _parse_order_file(f)
        assert infos["ID"] == "20260101-001"
        assert "P001" in commande

    def test_fichier_vide_retourne_dicts_vides(self, tmp_path):
        f = tmp_path / "commande_vide.json"
        f.write_text("{}", encoding="utf-8")
        infos, commande = _parse_order_file(f)
        assert infos == {}
        assert commande == {}

    def test_champs_manquants_retourne_dicts_vides(self, tmp_path):
        f = tmp_path / "commande_partielle.json"
        f.write_text('{"autre": "champ"}', encoding="utf-8")
        infos, commande = _parse_order_file(f)
        assert infos == {}
        assert commande == {}
