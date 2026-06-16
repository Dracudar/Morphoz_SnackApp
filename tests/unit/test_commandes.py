#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_commandes.py - Tests unitaires pour src/backend/data/commandes.py

Description:
    Tests unitaires pour le parsing des fichiers de commande.

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
from pathlib import Path

from src.backend.data.commandes import _parse_order_file


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
