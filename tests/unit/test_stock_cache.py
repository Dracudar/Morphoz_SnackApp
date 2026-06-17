#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_stock_cache.py - Tests unitaires pour StockCache

Description:
    Tests unitaires pour src/modules/stock/cache.py (StockCache).

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
from src.modules.stock.cache import StockCache


@pytest.fixture
def stock_file(tmp_path):
    data = {
        "Plats": {
            "Pizza": {
                "Pâte à pizza": {"Quantité": 10, "OutOfStock": False}
            },
            "Grillades": {
                "Poulet": {"Quantité": 5, "OutOfStock": False},
                "Entrecôte": {"Quantité": 0, "OutOfStock": True},
            },
        }
    }
    f = tmp_path / "stock.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


@pytest.fixture
def cache(stock_file):
    return StockCache(str(stock_file))


# ── Initialisation ────────────────────────────────────────────────────────────

class TestInit:
    def test_charge_quantite(self, cache):
        assert cache.get_quantite(["Plats", "Pizza", "Pâte à pizza"]) == 10

    def test_cache_independant_de_original(self, cache):
        cache._stock_cache["Plats"]["Pizza"]["Pâte à pizza"]["Quantité"] = 0
        assert cache._stock_original["Plats"]["Pizza"]["Pâte à pizza"]["Quantité"] == 10

    def test_data_retourne_cache(self, cache):
        assert cache.data is cache._stock_cache


# ── Décrémentation ────────────────────────────────────────────────────────────

class TestDecrementer:
    def test_decremente_une_unite(self, cache):
        cache.decrementer(["Plats", "Pizza", "Pâte à pizza"])
        assert cache.get_quantite(["Plats", "Pizza", "Pâte à pizza"]) == 9

    def test_retourne_true_si_suffisant(self, cache):
        assert cache.decrementer(["Plats", "Pizza", "Pâte à pizza"]) is True

    def test_retourne_false_si_insuffisant(self, cache):
        assert cache.decrementer(["Plats", "Grillades", "Entrecôte"]) is False

    def test_ne_decremente_pas_si_insuffisant(self, cache):
        cache.decrementer(["Plats", "Grillades", "Entrecôte"])
        assert cache.get_quantite(["Plats", "Grillades", "Entrecôte"]) == 0

    def test_passe_out_of_stock_a_zero(self, cache):
        for _ in range(5):
            cache.decrementer(["Plats", "Grillades", "Poulet"])
        assert cache.is_out_of_stock(["Plats", "Grillades", "Poulet"]) is True

    def test_decremente_n_unites(self, cache):
        cache.decrementer(["Plats", "Grillades", "Poulet"], 3)
        assert cache.get_quantite(["Plats", "Grillades", "Poulet"]) == 2

    def test_refuse_si_n_superieur_a_quantite(self, cache):
        assert cache.decrementer(["Plats", "Grillades", "Poulet"], 10) is False


# ── Incrémentation ────────────────────────────────────────────────────────────

class TestIncrementer:
    def test_incremente_une_unite(self, cache):
        cache.incrementer(["Plats", "Pizza", "Pâte à pizza"])
        assert cache.get_quantite(["Plats", "Pizza", "Pâte à pizza"]) == 11

    def test_retourne_true(self, cache):
        assert cache.incrementer(["Plats", "Pizza", "Pâte à pizza"]) is True

    def test_repasse_in_stock(self, cache):
        cache.incrementer(["Plats", "Grillades", "Entrecôte"])
        assert cache.is_out_of_stock(["Plats", "Grillades", "Entrecôte"]) is False

    def test_incremente_n_unites(self, cache):
        cache.incrementer(["Plats", "Grillades", "Poulet"], 3)
        assert cache.get_quantite(["Plats", "Grillades", "Poulet"]) == 8


# ── set_quantite ──────────────────────────────────────────────────────────────

class TestSetQuantite:
    def test_definit_valeur(self, cache):
        cache.set_quantite(["Plats", "Pizza", "Pâte à pizza"], 42)
        assert cache.get_quantite(["Plats", "Pizza", "Pâte à pizza"]) == 42

    def test_retourne_true_si_cle_valide(self, cache):
        assert cache.set_quantite(["Plats", "Pizza", "Pâte à pizza"], 5) is True

    def test_retourne_false_si_cle_invalide(self, cache):
        assert cache.set_quantite(["Plats", "Inexistant", "Item"], 5) is False

    def test_zero_met_out_of_stock(self, cache):
        cache.set_quantite(["Plats", "Grillades", "Poulet"], 0)
        assert cache.is_out_of_stock(["Plats", "Grillades", "Poulet"]) is True

    def test_positif_retire_out_of_stock(self, cache):
        cache.set_quantite(["Plats", "Grillades", "Entrecôte"], 5)
        assert cache.is_out_of_stock(["Plats", "Grillades", "Entrecôte"]) is False


# ── set_out_of_stock ──────────────────────────────────────────────────────────

class TestSetOutOfStock:
    def test_definit_true(self, cache):
        cache.set_out_of_stock(["Plats", "Pizza", "Pâte à pizza"], True)
        assert cache.is_out_of_stock(["Plats", "Pizza", "Pâte à pizza"]) is True

    def test_definit_false(self, cache):
        cache.set_out_of_stock(["Plats", "Grillades", "Entrecôte"], False)
        assert cache.is_out_of_stock(["Plats", "Grillades", "Entrecôte"]) is False

    def test_retourne_false_si_cle_invalide(self, cache):
        assert cache.set_out_of_stock(["Plats", "Inexistant", "Item"], True) is False


# ── Persistance ───────────────────────────────────────────────────────────────

class TestSave:
    def test_persiste_sur_disque(self, cache, stock_file):
        cache.decrementer(["Plats", "Pizza", "Pâte à pizza"], 3)
        cache.save()
        with open(str(stock_file), encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["Plats"]["Pizza"]["Pâte à pizza"]["Quantité"] == 7

    def test_met_a_jour_original(self, cache):
        cache.decrementer(["Plats", "Pizza", "Pâte à pizza"])
        cache.save()
        assert cache._stock_original["Plats"]["Pizza"]["Pâte à pizza"]["Quantité"] == 9


class TestResetCache:
    def test_restaure_valeurs_originales(self, cache):
        cache.decrementer(["Plats", "Pizza", "Pâte à pizza"], 5)
        cache.reset_cache()
        assert cache.get_quantite(["Plats", "Pizza", "Pâte à pizza"]) == 10

    def test_ne_modifie_pas_original(self, cache):
        cache.decrementer(["Plats", "Pizza", "Pâte à pizza"], 5)
        cache.reset_cache()
        assert cache._stock_original["Plats"]["Pizza"]["Pâte à pizza"]["Quantité"] == 10
