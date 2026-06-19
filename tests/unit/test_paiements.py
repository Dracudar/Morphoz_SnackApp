#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_paiements.py - Tests unitaires pour paiements

Description:
    Tests unitaires pour src/modules/commandes_saisie/backend/paiements.py.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.19

Date de modification:
    2026.06.19
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.modules.commandes_saisie.backend import paiements


# ── Données de test ───────────────────────────────────────────────────────────

def _commande_saisie(commandes_dir, id_commande="20260101-001"):
    """Écrit un fichier de commande 'En saisie' dans commandes_dir."""
    data = {
        "Informations": {
            "ID": id_commande,
            "Statut": "En saisie",
            "Montant": 8.5,
            "Type de paiement": "",
            "Prioritaire": False,
        },
        "Commande": {
            "P001": {
                "ID": f"{id_commande}-P001",
                "Plat": "Pizza",
                "Nom": "Margherita",
                "Statut": "En attente",
                "Prix": 8.5,
                "Composition": {},
            }
        },
    }
    chemin = commandes_dir / f"commande_{id_commande}.json"
    chemin.write_text(json.dumps(data), encoding="utf-8")
    return str(chemin)


def _lire(chemin):
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


@pytest.fixture
def mock_valider(monkeypatch):
    """Neutralise valider_commande (testée séparément dans test_gestion.py)."""
    mock = MagicMock()
    monkeypatch.setattr(paiements, "valider_commande", mock)
    return mock


# ── paiement_carte / paiement_especes / gratuit ──────────────────────────────

class TestPaiementCarte:
    def test_enregistre_le_mode_et_valide(self, commandes_dir, mock_valider):
        chemin = _commande_saisie(commandes_dir)
        paiements.paiement_carte(chemin)
        data = _lire(chemin)
        assert data["Informations"]["Type de paiement"] == "Carte"
        mock_valider.assert_called_once_with(chemin)

    def test_sans_effet_si_fichier_absent(self, tmp_path, mock_valider):
        paiements.paiement_carte(str(tmp_path / "inexistant.json"))
        mock_valider.assert_not_called()


class TestPaiementEspeces:
    def test_enregistre_le_mode_et_valide(self, commandes_dir, mock_valider):
        chemin = _commande_saisie(commandes_dir)
        paiements.paiement_especes(chemin)
        data = _lire(chemin)
        assert data["Informations"]["Type de paiement"] == "Espèces"
        mock_valider.assert_called_once_with(chemin)

    def test_sans_effet_si_fichier_absent(self, tmp_path, mock_valider):
        paiements.paiement_especes(str(tmp_path / "inexistant.json"))
        mock_valider.assert_not_called()


class TestGratuit:
    def test_enregistre_le_mode_et_valide(self, commandes_dir, mock_valider):
        chemin = _commande_saisie(commandes_dir)
        paiements.gratuit(chemin)
        data = _lire(chemin)
        assert data["Informations"]["Type de paiement"] == "Repas gratuit"
        mock_valider.assert_called_once_with(chemin)

    def test_sans_effet_si_fichier_absent(self, tmp_path, mock_valider):
        paiements.gratuit(str(tmp_path / "inexistant.json"))
        mock_valider.assert_not_called()
