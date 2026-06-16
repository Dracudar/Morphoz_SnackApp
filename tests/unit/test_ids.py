#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_ids.py - Tests unitaires pour src/backend/commandes/ids.py

Description:
    Tests unitaires pour DerniersIDCache et la génération d'identifiants
    de commande/plat journaliers.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.12

Date de modification:
    2026.06.16
"""

import json
from datetime import datetime

import pytest

from src.backend.commandes.ids import DerniersIDCache, PREFIXES_PLAT


def _today():
    return datetime.now().strftime("%Y%m%d")


# ── DerniersIDCache ───────────────────────────────────────────────────────────

class TestDerniersIDCacheInit:
    def test_init_vide_compteurs_a_zero(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 0
        for lettre in PREFIXES_PLAT.values():
            assert cache._data[lettre] == 0

    def test_init_depuis_fichier_existant(self, tmp_path):
        today = _today()
        data = {today: {"commande": 5, "pizza": 3, "grillade": 1,
                        "frites": 0, "salade composée": 0, "crêpe": 0}}
        (tmp_path / "derniers_ID.json").write_text(json.dumps(data), encoding="utf-8")
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 5
        assert cache._data["P"] == 3

    def test_init_migration_ancien_format_entier(self, tmp_path):
        today = _today()
        data = {today: 8}
        (tmp_path / "derniers_ID.json").write_text(json.dumps(data), encoding="utf-8")
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 8

    def test_init_depuis_ancien_nom_fichier(self, tmp_path):
        today = _today()
        data = {today: {"commande": 4, "pizza": 0, "grillade": 0,
                        "frites": 0, "salade composée": 0, "crêpe": 0}}
        (tmp_path / "dernier_id.json").write_text(json.dumps(data), encoding="utf-8")
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 4

    def test_init_autre_jour_ignore(self, tmp_path):
        data = {"20200101": {"commande": 99, "pizza": 0, "grillade": 0,
                             "frites": 0, "salade composée": 0, "crêpe": 0}}
        (tmp_path / "derniers_ID.json").write_text(json.dumps(data), encoding="utf-8")
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 0


class TestProchainIdCommande:
    def test_format_aaaammjj_tiret_000(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_commande()
        today = _today()
        assert id_ == f"{today}-001"

    def test_incremente_a_chaque_appel(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_commande()
        id2 = cache.prochain_id_commande()
        assert id2 == f"{_today()}-002"

    def test_persiste_apres_rechargement(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_commande()
        cache.prochain_id_commande()
        cache2 = DerniersIDCache(str(tmp_path))
        assert cache2._data["commande"] == 2


class TestDecrementerCommande:
    def test_decremente(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_commande()
        cache.decrementer_commande()
        assert cache._data["commande"] == 0

    def test_pas_en_dessous_de_zero(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.decrementer_commande()
        assert cache._data["commande"] == 0


class TestProchainIdPlat:
    @pytest.mark.parametrize("type_plat, prefixe_attendu", [
        ("pizza", "P"),
        ("grillade", "G"),
        ("frites", "F"),
        ("salade composée", "S"),
        ("crêpe", "C"),
    ])
    def test_prefixe_par_type(self, tmp_path, type_plat, prefixe_attendu):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_plat(type_plat)
        assert id_[0] == prefixe_attendu

    def test_format_lettre_trois_chiffres(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_plat("pizza")
        assert id_ == "P001"

    def test_incremente_independamment_par_type(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_plat("pizza")
        cache.prochain_id_plat("pizza")
        id_g = cache.prochain_id_plat("grillade")
        assert id_g == "G001"

    def test_type_inconnu_prefixe_x(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_plat("boisson")
        assert id_.startswith("X")

    def test_insensible_a_la_casse(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_plat("Pizza")
        assert id_ == "P001"
