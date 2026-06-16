#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_imprimante.py - Tests unitaires pour Imprimante

Description:
    Tests unitaires pour src/backend/config/imprimante.py.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.12

Date de modification:
    2026.06.16
"""

import pytest

from src.backend.config.imprimante import _parse_hex_or_int, get_printer_config


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


# ── get_printer_config ────────────────────────────────────────────────────────

class TestGetPrinterConfig:
    def test_retourne_valeurs_par_defaut_si_config_vide(self, monkeypatch):
        monkeypatch.setattr("src.backend.config.persistance._load_app_config", lambda: {})
        config = get_printer_config()
        assert config["vendor_id"] == 0x04B8
        assert config["product_id"] == 0x0E15
        assert config["interface"] == 0
        assert config["modele"] == "TM-T20II"

    def test_retourne_valeurs_personnalisees(self, monkeypatch):
        monkeypatch.setattr("src.backend.config.persistance._load_app_config", lambda: {
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
