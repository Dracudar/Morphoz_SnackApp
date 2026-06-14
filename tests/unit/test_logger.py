#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_logger.py - Tests unitaires pour logger

Description:
    Tests unitaires pour src/backend/logger.py.

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
from pathlib import Path

import src.backend.logger as logger_module
from src.backend.logger import (
    AJOUT_PLAT,
    ANNULATION_COMMANDE,
    ERREUR,
    VALIDATION_COMMANDE,
    _CATEGORIES,
    log,
    migrer_log_journalier,
)


@pytest.fixture
def logs_path(tmp_path, monkeypatch):
    """Configure le dossier de logs vers tmp_path et retourne le chemin."""
    d = tmp_path / "logs"
    d.mkdir()
    monkeypatch.setattr("src.backend.app_config.get_logs_folder_path", lambda: d)
    return d


# ── Constantes ────────────────────────────────────────────────────────────────

class TestConstantes:
    def test_evenements_ont_une_categorie(self):
        for evenement in (AJOUT_PLAT, VALIDATION_COMMANDE, ANNULATION_COMMANDE, ERREUR):
            assert evenement in _CATEGORIES

    def test_categories_connues(self):
        categories_valides = {"commande", "stock", "carte", "parametres", "systeme", "erreur"}
        for cat in _CATEGORIES.values():
            assert cat in categories_valides


# ── log() ─────────────────────────────────────────────────────────────────────

class TestLog:
    def test_cree_fichier_log(self, logs_path):
        log(AJOUT_PLAT, {"id_commande": "20260101-001"})
        fichiers = list(logs_path.glob("app_*.log"))
        assert len(fichiers) == 1

    def test_entree_est_json_valide(self, logs_path):
        log(AJOUT_PLAT, {"id_commande": "test"})
        fichier = next(logs_path.glob("app_*.log"))
        entree = json.loads(fichier.read_text(encoding="utf-8").strip())
        assert entree["evenement"] == AJOUT_PLAT

    def test_entree_contient_champs_requis(self, logs_path):
        log(VALIDATION_COMMANDE, {"test": True})
        fichier = next(logs_path.glob("app_*.log"))
        entree = json.loads(fichier.read_text(encoding="utf-8").strip())
        for champ in ("index", "timestamp", "categorie", "evenement", "details"):
            assert champ in entree

    def test_categorie_correcte(self, logs_path):
        log(AJOUT_PLAT, {})
        fichier = next(logs_path.glob("app_*.log"))
        entree = json.loads(fichier.read_text(encoding="utf-8").strip())
        assert entree["categorie"] == "commande"

    def test_details_vides_si_none(self, logs_path):
        log(ERREUR)
        fichier = next(logs_path.glob("app_*.log"))
        entree = json.loads(fichier.read_text(encoding="utf-8").strip())
        assert entree["details"] == {}

    def test_details_passes(self, logs_path):
        details = {"cle": "valeur", "nb": 42}
        log(AJOUT_PLAT, details)
        fichier = next(logs_path.glob("app_*.log"))
        entree = json.loads(fichier.read_text(encoding="utf-8").strip())
        assert entree["details"] == details

    def test_index_incremente(self, logs_path):
        log(AJOUT_PLAT, {})
        log(AJOUT_PLAT, {})
        log(AJOUT_PLAT, {})
        fichier = next(logs_path.glob("app_*.log"))
        lignes = [json.loads(l) for l in fichier.read_text(encoding="utf-8").strip().splitlines()]
        indices = [e["index"] for e in lignes]
        assert indices == [1, 2, 3]

    def test_plusieurs_entrees_dans_fichier(self, logs_path):
        log(AJOUT_PLAT, {})
        log(VALIDATION_COMMANDE, {})
        fichier = next(logs_path.glob("app_*.log"))
        lignes = fichier.read_text(encoding="utf-8").strip().splitlines()
        assert len(lignes) == 2


# ── migrer_log_journalier() ───────────────────────────────────────────────────

class TestMigrerLogJournalier:
    def _creer_log(self, dossier: Path, entrees: list):
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        f = dossier / f"app_{today}.log"
        with f.open("w", encoding="utf-8") as fh:
            for e in entrees:
                fh.write(json.dumps(e) + "\n")
        return f

    def test_deplace_si_destination_absente(self, tmp_path):
        ancien = tmp_path / "ancien_logs"
        ancien.mkdir()
        nouveau = tmp_path / "nouveau_logs"
        entrees = [{"index": 1, "timestamp": "2026-01-01T10:00:00",
                    "evenement": "TEST", "details": {}}]
        self._creer_log(ancien, entrees)
        migrer_log_journalier(ancien, nouveau)
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        assert (nouveau / f"app_{today}.log").exists()

    def test_fusionne_si_destination_presente(self, tmp_path):
        ancien = tmp_path / "ancien"
        ancien.mkdir()
        nouveau = tmp_path / "nouveau"
        nouveau.mkdir()
        e1 = {"index": 1, "timestamp": "2026-01-01T09:00:00",
              "evenement": "A", "details": {}}
        e2 = {"index": 1, "timestamp": "2026-01-01T10:00:00",
              "evenement": "B", "details": {}}
        self._creer_log(ancien, [e1])
        self._creer_log(nouveau, [e2])
        migrer_log_journalier(ancien, nouveau)
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        lignes = (nouveau / f"app_{today}.log").read_text(encoding="utf-8").strip().splitlines()
        assert len(lignes) == 2

    def test_rien_si_pas_de_fichier_source(self, tmp_path):
        ancien = tmp_path / "ancien"
        ancien.mkdir()
        nouveau = tmp_path / "nouveau"
        nouveau.mkdir()
        migrer_log_journalier(ancien, nouveau)
        assert list(nouveau.glob("*.log")) == []
