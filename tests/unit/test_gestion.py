"""
Tests unitaires pour src/modules/commandes_saisie/backend/gestion.py.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.modules.commandes_saisie.backend.gestion import (
    annuler_all_plats,
    annuler_commande,
    annuler_plat,
    set_prioritaire,
    valider_commande,
)


# ── Données de test ───────────────────────────────────────────────────────────

def _commande_saisie(commandes_dir, plats=None, id_commande="20260101-001"):
    """Écrit un fichier de commande 'En saisie' dans commandes_dir."""
    if plats is None:
        plats = {
            "P001": {
                "ID": f"{id_commande}-P001",
                "Plat": "Pizza",
                "Nom": "Margherita",
                "Statut": "En attente",
                "Prix": 8.5,
                "Composition": {},
            }
        }
    data = {
        "Informations": {
            "ID": id_commande,
            "Statut": "En saisie",
            "Montant": sum(p["Prix"] for p in plats.values()),
            "Prioritaire": False,
        },
        "Commande": plats,
    }
    chemin = commandes_dir / f"commande_{id_commande}.json"
    chemin.write_text(json.dumps(data), encoding="utf-8")
    return str(chemin)


def _commande_validee(commandes_dir, plats=None, id_commande="20260101-001"):
    """Écrit un fichier de commande 'Validée' dans commandes_dir/en_cours/."""
    if plats is None:
        plats = {
            "P001": {
                "ID": f"{id_commande}-P001",
                "Plat": "Pizza",
                "Nom": "Margherita",
                "Statut": "En préparation",
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


@pytest.fixture
def mocks_gestion(monkeypatch, id_cache):
    """Neutralise les effets de bord de gestion.py (logger, stock, printer)."""
    monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
    monkeypatch.setattr(
        "src.modules.commandes_saisie.backend.gestion.restaurer_stock_plat",
        lambda plat: None,
    )
    monkeypatch.setattr(
        "src.modules.commandes_saisie.backend.gestion.log_stock_restauration",
        lambda plat, id_cmd: None,
    )
    mock_cache = MagicMock()
    mock_cache.save = MagicMock()
    monkeypatch.setattr(
        "src.modules.commandes_saisie.backend.gestion.get_stock_cache",
        lambda: mock_cache,
    )
    monkeypatch.setattr(
        "src.modules.commandes_saisie.backend.gestion.print_ticket_recap",
        lambda *a: None,
    )
    monkeypatch.setattr(
        "src.modules.commandes_saisie.backend.gestion.print_ticket_cuisine",
        lambda *a: None,
    )
    return mock_cache


# ── set_prioritaire ───────────────────────────────────────────────────────────

class TestSetPrioritaire:
    def test_marque_prioritaire_true(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        set_prioritaire(chemin, True)
        data = json.loads(Path(chemin).read_text(encoding="utf-8"))
        assert data["Informations"]["Prioritaire"] is True

    def test_marque_prioritaire_false(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        set_prioritaire(chemin, True)
        set_prioritaire(chemin, False)
        data = json.loads(Path(chemin).read_text(encoding="utf-8"))
        assert data["Informations"]["Prioritaire"] is False

    def test_sans_effet_si_fichier_absent(self, tmp_path, mocks_gestion):
        set_prioritaire(str(tmp_path / "inexistant.json"), True)


# ── valider_commande ──────────────────────────────────────────────────────────

class TestValiderCommande:
    def test_deplace_vers_en_cours(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        valider_commande(chemin)
        assert not Path(chemin).exists()
        assert (commandes_dir / "en_cours" / Path(chemin).name).exists()

    def test_statut_passe_a_validee(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        nom = Path(chemin).name
        valider_commande(chemin)
        data = json.loads((commandes_dir / "en_cours" / nom).read_text(encoding="utf-8"))
        assert data["Informations"]["Statut"] == "Validée"

    def test_plats_passent_en_preparation(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        nom = Path(chemin).name
        valider_commande(chemin)
        data = json.loads((commandes_dir / "en_cours" / nom).read_text(encoding="utf-8"))
        for plat in data["Commande"].values():
            assert plat["Statut"] == "En préparation"

    def test_date_validation_renseignee(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        nom = Path(chemin).name
        valider_commande(chemin)
        data = json.loads((commandes_dir / "en_cours" / nom).read_text(encoding="utf-8"))
        date_val = data["Informations"]["Date de validation"]
        assert date_val[0] != "" and date_val[1] != ""


# ── annuler_plat ──────────────────────────────────────────────────────────────

class TestAnnulerPlatEnSaisie:
    def test_supprime_plat_unique_supprime_fichier(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        annuler_plat(chemin, "P001")
        assert not Path(chemin).exists()

    def test_garde_fichier_si_plusieurs_plats(self, commandes_dir, mocks_gestion):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                     "Statut": "En attente", "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                     "Statut": "En attente", "Prix": 9.5, "Composition": {}},
        }
        chemin = _commande_saisie(commandes_dir, plats=plats)
        annuler_plat(chemin, "P001")
        assert Path(chemin).exists()
        data = json.loads(Path(chemin).read_text(encoding="utf-8"))
        assert "P001" not in data["Commande"]

    def test_recalcule_montant(self, commandes_dir, mocks_gestion):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                     "Statut": "En attente", "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                     "Statut": "En attente", "Prix": 9.5, "Composition": {}},
        }
        chemin = _commande_saisie(commandes_dir, plats=plats)
        annuler_plat(chemin, "P001")
        data = json.loads(Path(chemin).read_text(encoding="utf-8"))
        assert data["Informations"]["Montant"] == pytest.approx(9.5)

    def test_accepte_id_complet(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        annuler_plat(chemin, "20260101-001-P001")
        assert not Path(chemin).exists()

    def test_sans_effet_si_plat_absent(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        annuler_plat(chemin, "X999")
        assert Path(chemin).exists()


class TestAnnulerPlatValidee:
    def test_marque_annule(self, commandes_dir, mocks_gestion):
        # 2 plats : annuler P001 laisse G001 → fichier reste en place
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                     "Statut": "En préparation", "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                     "Statut": "En préparation", "Prix": 9.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        annuler_plat(chemin, "P001")
        data = json.loads(Path(chemin).read_text(encoding="utf-8"))
        assert data["Commande"]["P001"]["Statut"] == "Annulé"

    def test_deplace_si_tous_annules(self, commandes_dir, mocks_gestion):
        # annuler_commande crée le dossier annulee/ à côté du fichier (en_cours/)
        chemin = _commande_validee(commandes_dir)
        nom = Path(chemin).name
        annuler_plat(chemin, "P001")
        assert not Path(chemin).exists()
        assert (commandes_dir / "en_cours" / "annulee" / nom).exists()

    def test_montant_exclu_plat_annule(self, commandes_dir, mocks_gestion):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                     "Statut": "En préparation", "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                     "Statut": "En préparation", "Prix": 9.5, "Composition": {}},
        }
        chemin = _commande_validee(commandes_dir, plats=plats)
        annuler_plat(chemin, "P001")
        data = json.loads(Path(chemin).read_text(encoding="utf-8"))
        assert data["Informations"]["Montant"] == pytest.approx(9.5)


# ── annuler_all_plats ─────────────────────────────────────────────────────────

class TestAnnulerAllPlats:
    def test_supprime_fichier_en_saisie(self, commandes_dir, mocks_gestion):
        chemin = _commande_saisie(commandes_dir)
        annuler_all_plats(chemin)
        assert not Path(chemin).exists()

    def test_supprime_fichier_avec_plusieurs_plats_en_saisie(self, commandes_dir, mocks_gestion):
        plats = {
            "P001": {"ID": "20260101-001-P001", "Plat": "Pizza", "Nom": "A",
                     "Statut": "En attente", "Prix": 8.5, "Composition": {}},
            "G001": {"ID": "20260101-001-G001", "Plat": "Grillade", "Nom": "B",
                     "Statut": "En attente", "Prix": 9.5, "Composition": {}},
        }
        chemin = _commande_saisie(commandes_dir, plats=plats)
        annuler_all_plats(chemin)
        assert not Path(chemin).exists()

    def test_deplace_en_annulee_si_validee(self, commandes_dir, mocks_gestion):
        # annuler_commande déplace vers annulee/ relatif à la position du fichier (en_cours/)
        chemin = _commande_validee(commandes_dir)
        nom = Path(chemin).name
        annuler_all_plats(chemin)
        assert not Path(chemin).exists()
        assert (commandes_dir / "en_cours" / "annulee" / nom).exists()
