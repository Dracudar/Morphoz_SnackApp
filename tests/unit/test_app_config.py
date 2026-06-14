"""
Tests unitaires pour src/backend/app_config.py.
"""

import json
import pytest
from pathlib import Path

from src.backend.app_config import (
    _load_json_file,
    _parse_hex_or_int,
    _write_json_file,
    get_default_config,
    get_print_options,
    get_printer_config,
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
