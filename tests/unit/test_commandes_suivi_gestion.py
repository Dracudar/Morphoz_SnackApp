#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_commandes_suivi_gestion.py - Tests unitaires pour commandes_suivi_gestion

Description:
    Tests unitaires pour src/modules/commandes_suivi/backend/commandes_suivi_gestion.py,
    en particulier la préservation du comportement métier après l'ajout du verrouillage
    par fichier (accès concurrent multi-postes).

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

from src.modules.commandes_suivi.backend import commandes_suivi_gestion as suivi
from src.modules.commandes_suivi.backend.commandes_suivi_gestion import (
    annuler_commande_complete,
    annuler_plat_valide,
    livrer_plat,
    marquer_plat_livre,
    marquer_plat_pret,
    plat_prêt,
    retour_preparation,
    retour_pret,
    terminer_commande,
)


# ── Données de test ───────────────────────────────────────────────────────────

def _commande_validee(commandes_dir, plats=None, id_commande="20260101-001"):
    """Écrit un fichier de commande 'Validée' dans commandes_dir/en_cours/."""
    if plats is None:
        plats = {
            "P001": {
                "ID": f"{id_commande}-P001",
                "Plat": "Pizza",
                "Nom": "Margherita",
                "Statut": "En préparation",
                "Date de mise en livraison": ["", ""],
                "Date de livraison": ["", ""],
                "Date d'annulation": ["", ""],
                "Prix": 8.5,
                "Composition": {},
            }
        }
    data = {
        "Informations": {
            "ID": id_commande,
            "Statut": "Validée",
            "Montant": sum(p["Prix"] for p in plats.values()),
            "Prioritaire": False,
        },
        "Commande": plats,
    }
    en_cours = commandes_dir / "en_cours"
    en_cours.mkdir(exist_ok=True)
    chemin = en_cours / f"commande_{id_commande}.json"
    chemin.write_text(json.dumps(data), encoding="utf-8")
    return str(chemin)


def _lire(chemin):
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


@pytest.fixture
def mocks_suivi(monkeypatch):
    """Neutralise les effets de bord (logger, stock, transfert) pour isoler la logique de statut."""
    monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
    monkeypatch.setattr(suivi, "restaurer_stock_plat", lambda plat: None)
    monkeypatch.setattr(suivi, "log_stock_restauration", lambda plat, id_cmd: None)
    mock_cache = MagicMock()
    monkeypatch.setattr(suivi, "get_stock_cache", lambda: mock_cache)
    # Par défaut, aucun candidat de transfert (comportement testé séparément).
    monkeypatch.setattr(suivi, "trouver_candidat_transfert", lambda plat_ref, chemin: None)
    return mock_cache


# ── plat_prêt ──────────────────────────────────────────────────────────────────

class TestPlatPret:
    def test_change_statut_et_rafraichit(self, commandes_dir, mocks_suivi):
        chemin = _commande_validee(commandes_dir)
        refresh = MagicMock()
        plat_prêt(None, chemin, "20260101-001-P001", refresh)
        data = _lire(chemin)
        assert data["Commande"]["P001"]["Statut"] == "Prêt"
        refresh.assert_called_once()

    def test_ignore_si_mauvais_statut(self, commandes_dir, mocks_suivi):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Prêt", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        refresh = MagicMock()
        plat_prêt(None, chemin, "20260101-001-P001", refresh)
        refresh.assert_not_called()


# ── livrer_plat / terminer_commande ──────────────────────────────────────────

class TestLivrerPlat:
    def test_change_statut_et_termine_commande(self, commandes_dir, mocks_suivi):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Prêt", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        nom = Path(chemin).name
        refresh = MagicMock()
        livrer_plat(None, chemin, "20260101-001-P001", refresh)
        assert not Path(chemin).exists()
        terminee = commandes_dir / "terminee" / nom
        assert terminee.exists()
        data = _lire(terminee)
        assert data["Commande"]["P001"]["Statut"] == "Livré"
        assert data["Informations"]["Statut"] == "Terminée"
        refresh.assert_called_once()

    def test_ne_termine_pas_si_plat_restant_actif(self, commandes_dir, mocks_suivi):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Prêt", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                      "Statut": "En préparation", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 9.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        refresh = MagicMock()
        livrer_plat(None, chemin, "20260101-001-P001", refresh)
        assert Path(chemin).exists()
        data = _lire(chemin)
        assert data["Commande"]["P001"]["Statut"] == "Livré"
        assert data["Informations"]["Statut"] == "Validée"


class TestTerminerCommande:
    def test_sans_effet_si_fichier_absent(self, tmp_path, mocks_suivi):
        terminer_commande(str(tmp_path / "inexistant.json"))


# ── Actions historique ────────────────────────────────────────────────────────

class TestMarquerPlatPret:
    def test_marque_pret(self, commandes_dir, mocks_suivi):
        chemin = _commande_validee(commandes_dir)
        assert marquer_plat_pret(chemin, "20260101-001-P001") is True
        data = _lire(chemin)
        assert data["Commande"]["P001"]["Statut"] == "Prêt"

    def test_retourne_false_si_mauvais_statut(self, commandes_dir, mocks_suivi):
        chemin = _commande_validee(commandes_dir)
        # Déjà "En préparation" -> "Prêt" est valide une première fois, pas une seconde.
        marquer_plat_pret(chemin, "20260101-001-P001")
        assert marquer_plat_pret(chemin, "20260101-001-P001") is False


class TestMarquerPlatLivre:
    def test_marque_livre_et_termine(self, commandes_dir, mocks_suivi):
        chemin = _commande_validee(commandes_dir)
        nom = Path(chemin).name
        assert marquer_plat_livre(chemin, "20260101-001-P001") is True
        assert not Path(chemin).exists()
        assert (commandes_dir / "terminee" / nom).exists()


# ── annuler_plat_valide ───────────────────────────────────────────────────────

class TestAnnulerPlatValideEnPreparation:
    def test_marque_annule_et_restaure_stock(self, commandes_dir, mocks_suivi):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "En préparation", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                      "Statut": "En préparation", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 9.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        assert annuler_plat_valide(chemin, "20260101-001-P001") is True
        data = _lire(chemin)
        assert data["Commande"]["P001"]["Statut"] == "Annulé"
        mocks_suivi.save.assert_called_once()

    def test_finalise_en_annulee_si_tous_annules(self, commandes_dir, mocks_suivi):
        chemin = _commande_validee(commandes_dir)
        nom = Path(chemin).name
        annuler_plat_valide(chemin, "20260101-001-P001")
        assert not Path(chemin).exists()
        assert (commandes_dir / "annulee" / nom).exists()


class TestAnnulerPlatValidePret:
    def test_sans_candidat_marque_non_livre(self, commandes_dir, mocks_suivi):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Prêt", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        nom = Path(chemin).name
        assert annuler_plat_valide(chemin, "20260101-001-P001") is True
        # Seul plat de la commande -> état terminal mixte (Non livré) -> commande terminée.
        assert not Path(chemin).exists()
        data = _lire(commandes_dir / "terminee" / nom)
        assert data["Commande"]["P001"]["Statut"] == "Non livré"

    def test_avec_candidat_transfere_et_annule(self, commandes_dir, mocks_suivi, monkeypatch):
        plats_source = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Prêt", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
        }
        chemin_source = _commande_validee(commandes_dir, plats=plats_source, id_commande="20260101-001")
        nom_source = Path(chemin_source).name

        plats_dest = {
            "P002": {"ID": "20260101-002-P002", "Plat": "Pizza", "Nom": "A",
                      "Statut": "En préparation", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
        }
        chemin_dest = _commande_validee(commandes_dir, plats=plats_dest, id_commande="20260101-002")

        monkeypatch.setattr(
            suivi, "trouver_candidat_transfert",
            lambda plat_ref, chemin: (chemin_dest, "20260101-002-P002"),
        )

        assert annuler_plat_valide(chemin_source, "20260101-001-P001") is True

        # Seul plat de la commande source, transféré puis annulé -> commande annulée.
        assert not Path(chemin_source).exists()
        data_source = _lire(commandes_dir / "annulee" / nom_source)
        assert data_source["Commande"]["P001"]["Statut"] == "Annulé"

        data_dest = _lire(chemin_dest)
        assert data_dest["Commande"]["P002"]["Statut"] == "Prêt"


# ── retour_preparation ────────────────────────────────────────────────────────

class TestRetourPreparation:
    def _plat_pret(self, commandes_dir):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Prêt", "Date de mise en livraison": ["01/01/2026", "12:00"],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
        }
        return _commande_validee(commandes_dir, plats=plats)

    def test_revient_en_preparation_et_rafraichit(self, commandes_dir, mocks_suivi):
        chemin = self._plat_pret(commandes_dir)
        refresh = MagicMock()
        retour_preparation(None, chemin, "20260101-001-P001", refresh)
        data = _lire(chemin)
        assert data["Commande"]["P001"]["Statut"] == "En préparation"
        assert data["Commande"]["P001"]["Date de mise en livraison"] == ["", ""]
        refresh.assert_called_once()

    def test_ignore_si_statut_pas_pret(self, commandes_dir, mocks_suivi):
        chemin = _commande_validee(commandes_dir)  # statut initial "En préparation"
        refresh = MagicMock()
        retour_preparation(None, chemin, "20260101-001-P001", refresh)
        refresh.assert_not_called()
        data = _lire(chemin)
        assert data["Commande"]["P001"]["Statut"] == "En préparation"


# ── retour_pret ───────────────────────────────────────────────────────────────

class TestRetourPret:
    def _commande_avec_plat_livre(self, commandes_dir, statut_commande="Validée", dossier="en_cours"):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Livré", "Date de mise en livraison": ["01/01/2026", "11:00"],
                      "Date de livraison": ["01/01/2026", "12:00"], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                      "Statut": "En préparation", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 9.5, "Composition": {}},
        }
        data = {
            "Informations": {
                "ID": "20260101-001",
                "Statut": statut_commande,
                "Montant": 18.0,
                "Prioritaire": False,
            },
            "Commande": plats,
        }
        sous_dossier = commandes_dir / dossier
        sous_dossier.mkdir(exist_ok=True)
        chemin = sous_dossier / "commande_20260101-001.json"
        chemin.write_text(json.dumps(data), encoding="utf-8")
        return str(chemin)

    def _commande_terminee(self, commandes_dir):
        """Commande avec un unique plat 'Livré', statut 'Terminée', dans /terminee/."""
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Livré", "Date de mise en livraison": ["01/01/2026", "11:00"],
                      "Date de livraison": ["01/01/2026", "12:00"], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
        }
        data = {
            "Informations": {
                "ID": "20260101-001",
                "Statut": "Terminée",
                "Date de finalisation": ["01/01/2026", "12:00"],
                "Montant": 8.5,
                "Prioritaire": False,
            },
            "Commande": plats,
        }
        terminee = commandes_dir / "terminee"
        terminee.mkdir(exist_ok=True)
        chemin = terminee / "commande_20260101-001.json"
        chemin.write_text(json.dumps(data), encoding="utf-8")
        return str(chemin)

    def test_plat_livre_revient_a_pret(self, commandes_dir, mocks_suivi):
        chemin = self._commande_avec_plat_livre(commandes_dir)
        assert retour_pret(chemin, "20260101-001-P001") is True
        data = _lire(chemin)
        assert data["Commande"]["P001"]["Statut"] == "Prêt"
        assert data["Commande"]["P001"]["Date de livraison"] == ["", ""]
        assert data["Informations"]["Statut"] == "Validée"

    def test_retourne_false_si_statut_pas_livre(self, commandes_dir, mocks_suivi):
        chemin = self._commande_avec_plat_livre(commandes_dir)
        assert retour_pret(chemin, "20260101-001-G001") is False

    def test_rouvre_commande_terminee(self, commandes_dir, mocks_suivi):
        chemin = self._commande_terminee(commandes_dir)
        nom = Path(chemin).name
        assert retour_pret(chemin, "20260101-001-P001") is True
        assert not Path(chemin).exists()
        chemin_en_cours = commandes_dir / "en_cours" / nom
        assert chemin_en_cours.exists()
        data = _lire(chemin_en_cours)
        assert data["Commande"]["P001"]["Statut"] == "Prêt"
        assert data["Informations"]["Statut"] == "Validée"
        assert data["Informations"]["Date de finalisation"] == ["", ""]


class TestAnnulerCommandeComplete:
    def test_annule_tous_les_plats_actifs(self, commandes_dir, mocks_suivi):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "En préparation", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                      "Statut": "En préparation", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 9.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        nom = Path(chemin).name
        assert annuler_commande_complete(chemin) is True
        assert not Path(chemin).exists()
        assert (commandes_dir / "annulee" / nom).exists()

    def test_retourne_false_si_aucun_plat_actif(self, commandes_dir, mocks_suivi):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                      "Statut": "Livré", "Date de mise en livraison": ["", ""],
                      "Date de livraison": ["", ""], "Date d'annulation": ["", ""],
                      "Prix": 8.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        assert annuler_commande_complete(chemin) is False
