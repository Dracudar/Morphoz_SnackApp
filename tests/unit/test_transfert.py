#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_transfert.py - Tests unitaires pour src/backend/commandes/transfert.py

Description:
    Tests unitaires pour la comparaison de plats identiques utilisée lors
    de la recherche d'un candidat de transfert.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.12

Date de modification:
    2026.06.16
"""

from src.backend.commandes.transfert import plats_identiques


# ── plats_identiques ──────────────────────────────────────────────────────────

class TestPlatsIdentiques:
    def _plat(self, **kwargs):
        base = {"Plat": "Pizza", "Recette": "Margherita",
                "Nom": "Margherita", "Composition": {"tomate": 1}}
        base.update(kwargs)
        return base

    def test_identiques(self):
        plat = self._plat()
        assert plats_identiques(plat, plat.copy()) is True

    def test_type_different(self):
        a = self._plat(Plat="Pizza")
        b = self._plat(Plat="Grillade")
        assert plats_identiques(a, b) is False

    def test_recette_differente(self):
        a = self._plat(Recette="Margherita")
        b = self._plat(Recette="4 Fromages")
        assert plats_identiques(a, b) is False

    def test_nom_different(self):
        a = self._plat(Nom="A")
        b = self._plat(Nom="B")
        assert plats_identiques(a, b) is False

    def test_composition_differente(self):
        a = self._plat(Composition={"tomate": 1})
        b = self._plat(Composition={"tomate": 2})
        assert plats_identiques(a, b) is False

    def test_composition_identique_ordre_different(self):
        a = self._plat(Composition={"tomate": 1, "mozzarella": 2})
        b = self._plat(Composition={"mozzarella": 2, "tomate": 1})
        assert plats_identiques(a, b) is True
