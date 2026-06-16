#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_stock_utils.py - Tests unitaires pour src/backend/commandes/stock_utils.py

Description:
    Tests unitaires pour le chargement de fichiers JSON de commande avec
    gestion des erreurs (quarantaine des fichiers corrompus).

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

from src.backend.commandes.stock_utils import charger_fichier_commande


# ── charger_fichier_commande ──────────────────────────────────────────────────

class TestChargerFichierCommande:
    def test_retourne_none_si_inexistant(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
        result = charger_fichier_commande(str(tmp_path / "inexistant.json"))
        assert result is None

    def test_retourne_contenu_si_valide(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
        data = {"Informations": {"ID": "20260101-001"}, "Commande": {}}
        f = tmp_path / "commande_test.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        result = charger_fichier_commande(str(f))
        assert result == data

    def test_retourne_none_si_json_invalide(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
        f = tmp_path / "commande_bad.json"
        f.write_text("{{invalid json", encoding="utf-8")
        result = charger_fichier_commande(str(f))
        assert result is None

    def test_deplace_fichier_corrompu(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
        f = tmp_path / "commande_bad.json"
        f.write_text("{{invalid json", encoding="utf-8")
        charger_fichier_commande(str(f))
        assert (tmp_path / "corrompu" / "commande_bad.json").exists()
        assert not f.exists()
