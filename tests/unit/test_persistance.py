#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_persistance.py - Tests unitaires pour Persistance

Description:
    Tests unitaires pour src/backend/config/persistance.py.

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
import pytest
from pathlib import Path

from src.backend.config.persistance import (
    _load_json_file,
    _write_json_file,
    get_default_config,
)


# ── _load_json_file ───────────────────────────────────────────────────────────

class TestLoadJsonFile:
    def test_charge_fichier_valide(self, tmp_path):
        data = {"cle": "valeur", "nb": 42}
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        assert _load_json_file(f) == data

    def test_retourne_dict_vide_si_absent(self, tmp_path):
        assert _load_json_file(tmp_path / "inexistant.json") == {}

    def test_retourne_dict_vide_si_json_invalide(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{{not valid json", encoding="utf-8")
        assert _load_json_file(f) == {}

    def test_retourne_dict_vide_si_pas_un_dict(self, tmp_path):
        f = tmp_path / "list.json"
        f.write_text("[1, 2, 3]", encoding="utf-8")
        assert _load_json_file(f) == {}


# ── _write_json_file ──────────────────────────────────────────────────────────

class TestWriteJsonFile:
    def test_ecrit_fichier(self, tmp_path):
        data = {"test": 123}
        f = tmp_path / "out.json"
        result = _write_json_file(f, data)
        assert result is True
        assert json.loads(f.read_text(encoding="utf-8")) == data

    def test_cree_dossiers_parents(self, tmp_path):
        f = tmp_path / "sous" / "dossier" / "out.json"
        _write_json_file(f, {"x": 1})
        assert f.exists()

    def test_retourne_true_si_succes(self, tmp_path):
        assert _write_json_file(tmp_path / "f.json", {}) is True


# ── get_default_config ────────────────────────────────────────────────────────

class TestGetDefaultConfig:
    def test_contient_cles_requises(self):
        config = get_default_config()
        assert "data_folder" in config
        assert "imprimante" in config
        assert "impression" in config

    def test_impression_toutes_actives_par_defaut(self):
        config = get_default_config()
        assert config["impression"]["impression_active"] is True
        assert config["impression"]["ticket_client"] is True
        assert config["impression"]["ticket_cuisine"] is True

    def test_imprimante_contient_champs_requis(self):
        config = get_default_config()
        for champ in ("vendor_id", "product_id", "interface", "modele"):
            assert champ in config["imprimante"]
