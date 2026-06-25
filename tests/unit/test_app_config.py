#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_app_config.py - Tests unitaires pour AppConfig

Description:
    Tests unitaires pour src/backend/app_config.py.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.06.12

Date de modification:
    2026.06.25
"""

import json
import pytest
from pathlib import Path

from src.backend.app_config import (
    _load_json_file,
    _parse_hex_or_int,
    _write_json_file,
    data_folder_est_configure,
    get_data_folder_brut,
    get_default_config,
    get_print_options,
    get_printer_config,
    initialiser_dossier_data,
    save_app_config,
)


# ── _parse_hex_or_int ─────────────────────────────────────────────────────────

class TestParseHexOrInt:
    def test_entier_direct(self):
        assert _parse_hex_or_int(1208, 0) == 1208

    def test_chaine_hexadecimale_minuscule(self):
        assert _parse_hex_or_int("0x04b8", 0) == 0x04B8

    def test_chaine_hexadecimale_majuscule(self):
        assert _parse_hex_or_int("0x04B8", 0) == 0x04B8

    def test_chaine_hexadecimale_0X(self):
        assert _parse_hex_or_int("0X0E15", 0) == 0x0E15

    def test_chaine_decimal(self):
        assert _parse_hex_or_int("1208", 0) == 1208

    def test_chaine_invalide_retourne_defaut(self):
        assert _parse_hex_or_int("invalid", 42) == 42

    def test_type_invalide_retourne_defaut(self):
        assert _parse_hex_or_int(None, 99) == 99


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


# ── get_printer_config ────────────────────────────────────────────────────────

class TestGetPrinterConfig:
    def test_retourne_valeurs_par_defaut_si_config_vide(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {})
        config = get_printer_config()
        assert config["vendor_id"] == 0x04B8
        assert config["product_id"] == 0x0E15
        assert config["interface"] == 0
        assert config["modele"] == "TM-T20II"

    def test_retourne_valeurs_personnalisees(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {
            "imprimante": {
                "vendor_id": "0x1234",
                "product_id": "0x5678",
                "interface": 1,
                "modele": "TestPrinter",
            }
        })
        config = get_printer_config()
        assert config["vendor_id"] == 0x1234
        assert config["product_id"] == 0x5678
        assert config["interface"] == 1
        assert config["modele"] == "TestPrinter"


# ── get_print_options ─────────────────────────────────────────────────────────

class TestGetPrintOptions:
    def test_defauts_si_config_vide(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {})
        opts = get_print_options()
        assert opts["impression_active"] is True
        assert opts["ticket_client"] is True
        assert opts["ticket_cuisine"] is True

    def test_valeurs_personnalisees(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {
            "impression": {
                "impression_active": False,
                "ticket_client": True,
                "ticket_cuisine": False,
            }
        })
        opts = get_print_options()
        assert opts["impression_active"] is False
        assert opts["ticket_client"] is True
        assert opts["ticket_cuisine"] is False


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

    def test_data_folder_est_chaine_vide(self):
        assert get_default_config()["data_folder"] == ""


# ── data_folder_est_configure ─────────────────────────────────────────────────

class TestDataFolderEstConfigure:
    def test_retourne_false_si_absent(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {})
        assert data_folder_est_configure() is False

    def test_retourne_false_si_chaine_vide(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {"data_folder": ""})
        assert data_folder_est_configure() is False

    def test_retourne_false_si_espaces_seuls(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {"data_folder": "   "})
        assert data_folder_est_configure() is False

    def test_retourne_true_si_chemin_defini(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {"data_folder": "/chemin/data"})
        assert data_folder_est_configure() is True


# ── get_data_folder_brut ──────────────────────────────────────────────────────

class TestGetDataFolderBrut:
    def test_retourne_chaine_vide_si_absent(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {})
        assert get_data_folder_brut() == ""

    def test_retourne_chaine_vide_si_vide(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {"data_folder": ""})
        assert get_data_folder_brut() == ""

    def test_retourne_chemin_stripe(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {"data_folder": "  /mon/dossier  "})
        assert get_data_folder_brut() == "/mon/dossier"


# ── initialiser_dossier_data ──────────────────────────────────────────────────

class TestInitialiserDossierData:
    def test_retourne_true_sans_creer_si_non_configure(self, monkeypatch):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {"data_folder": ""})
        creations = []
        monkeypatch.setattr("src.backend.app_config._create_data_structure", lambda p: creations.append(p) or True)
        assert initialiser_dossier_data() is True
        assert creations == []

    def test_cree_structure_si_configure(self, monkeypatch, tmp_path):
        monkeypatch.setattr("src.backend.app_config._load_app_config", lambda: {"data_folder": str(tmp_path)})
        creations = []
        monkeypatch.setattr("src.backend.app_config._create_data_structure", lambda p: creations.append(p) or True)
        initialiser_dossier_data()
        assert len(creations) == 1


# ── save_app_config ───────────────────────────────────────────────────────────

class TestSaveAppConfig:
    def _appeler(self, monkeypatch, data_folder, creations, ecritures):
        monkeypatch.setattr("src.backend.app_config._create_data_structure", lambda p: creations.append(p) or True)
        monkeypatch.setattr("src.backend.app_config._write_json_file", lambda p, d: ecritures.append(d) or True)
        return save_app_config(data_folder, "0x04B8", "0x0E15", 0, "TM-T20II", True, True, True)

    def test_ne_cree_pas_structure_si_data_folder_vide(self, monkeypatch):
        creations, ecritures = [], []
        self._appeler(monkeypatch, "", creations, ecritures)
        assert creations == []
        assert len(ecritures) == 1

    def test_cree_structure_si_data_folder_defini(self, monkeypatch, tmp_path):
        creations, ecritures = [], []
        self._appeler(monkeypatch, str(tmp_path), creations, ecritures)
        assert len(creations) == 1

    def test_persiste_data_folder_vide_comme_chaine_vide(self, monkeypatch):
        creations, ecritures = [], []
        self._appeler(monkeypatch, "", creations, ecritures)
        assert ecritures[0]["data_folder"] == ""

    def test_persiste_data_folder_defini(self, monkeypatch, tmp_path):
        creations, ecritures = [], []
        self._appeler(monkeypatch, str(tmp_path), creations, ecritures)
        assert ecritures[0]["data_folder"] == str(tmp_path)
