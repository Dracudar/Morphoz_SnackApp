#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_categories.py - Tests unitaires pour src/backend/data/categories.py

Description:
    Tests unitaires pour la normalisation de texte/état et la construction
    des catégories de menu.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.12

Date de modification:
    2026.06.16
"""

from src.backend.data.categories import (
    _normalize_text,
    _normalized_state,
    get_menu_categories,
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
        monkeypatch.setattr("src.backend.data.categories.get_card_data", lambda: card_data)
        monkeypatch.setattr("src.backend.data.categories._resolve_category_icon", lambda *a: None)

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
