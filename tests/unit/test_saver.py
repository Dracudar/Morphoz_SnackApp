#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_saver.py - Tests unitaires pour saver

Description:
    Tests unitaires pour src/modules/commandes_saisie/backend/saver.py.

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
from collections import OrderedDict

from src.modules.commandes_saisie.backend.saver import (
    _sort_key_plat,
    creer_dict_plat,
    initialiser_dossiers_commandes,
    MAJ_commande,
)


# ── _sort_key_plat ────────────────────────────────────────────────────────────

class TestSortKeyPlat:
    def test_lettre_et_numero(self):
        assert _sort_key_plat("P030") == ("P", 30)

    def test_grillade(self):
        assert _sort_key_plat("G001") == ("G", 1)

    def test_numero_a_trois_chiffres(self):
        assert _sort_key_plat("F999") == ("F", 999)

    def test_chaine_vide(self):
        assert _sort_key_plat("") == ("", 0)

    def test_chaine_invalide(self):
        assert _sort_key_plat("abc") == ("", 0)

    def test_ordre_de_tri(self):
        ids = ["P002", "G001", "C003", "P001"]
        trie = sorted(ids, key=_sort_key_plat)
        assert trie == ["C003", "G001", "P001", "P002"]


# ── creer_dict_plat ───────────────────────────────────────────────────────────

class TestCreerDictPlat:
    def _plat_base(self, type_plat="Grillade"):
        return {
            "Plat": type_plat,
            "Nom": "Poulet grillé",
            "Prix": 9.5,
            "Composition": {"Viandes": {"Poulet": 1}},
        }

    def test_champs_obligatoires_presents(self):
        plat = creer_dict_plat("20260101-001-G001", self._plat_base())
        for champ in ("ID", "Plat", "Nom", "Statut", "Prix", "Composition"):
            assert champ in plat

    def test_statut_en_attente(self):
        plat = creer_dict_plat("20260101-001-G001", self._plat_base())
        assert plat["Statut"] == "En attente"

    def test_id_assigne(self):
        plat_id = "20260101-001-G001"
        plat = creer_dict_plat(plat_id, self._plat_base())
        assert plat["ID"] == plat_id

    def test_dates_vides_par_defaut(self):
        plat = creer_dict_plat("id", self._plat_base())
        assert plat["Date de mise en livraison"] == ["", ""]
        assert plat["Date de livraison"] == ["", ""]

    def test_pizza_contient_recette(self):
        plat_pizza = {**self._plat_base("Pizza"), "Recette": "Margherita"}
        result = creer_dict_plat("20260101-001-P001", plat_pizza)
        assert "Recette" in result
        assert result["Recette"] == "Margherita"

    def test_pizza_recette_entre_plat_et_nom(self):
        plat_pizza = {**self._plat_base("Pizza"), "Recette": "4 Fromages"}
        result = creer_dict_plat("id", plat_pizza)
        cles = list(result.keys())
        idx_plat = cles.index("Plat")
        idx_recette = cles.index("Recette")
        idx_nom = cles.index("Nom")
        assert idx_plat < idx_recette < idx_nom

    def test_non_pizza_sans_recette(self):
        plat = creer_dict_plat("id", self._plat_base("Grillade"))
        assert "Recette" not in plat

    def test_pizza_retourne_ordered_dict(self):
        plat_pizza = {**self._plat_base("Pizza"), "Recette": "test"}
        result = creer_dict_plat("id", plat_pizza)
        assert isinstance(result, OrderedDict)


# ── initialiser_dossiers_commandes ────────────────────────────────────────────

class TestInitialiserDossiers:
    def test_cree_structure_complete(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
        commandes = tmp_path / "commandes"
        logs = tmp_path / "logs"
        initialiser_dossiers_commandes(str(commandes), str(logs))
        assert commandes.exists()
        assert logs.exists()
        for sous_dossier in ("en_cours", "terminee", "annulee", "corrompu"):
            assert (commandes / sous_dossier).exists()

    def test_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
        commandes = tmp_path / "commandes"
        logs = tmp_path / "logs"
        initialiser_dossiers_commandes(str(commandes), str(logs))
        initialiser_dossiers_commandes(str(commandes), str(logs))
        assert commandes.exists()


# ── MAJ_commande ──────────────────────────────────────────────────────────────

@pytest.fixture
def env_commandes(tmp_path, monkeypatch, id_cache):
    """Configure l'environnement de test pour MAJ_commande."""
    monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
    commandes = tmp_path / "commandes"
    commandes.mkdir(exist_ok=True)
    logs = tmp_path / "logs"
    logs.mkdir(exist_ok=True)
    return commandes, logs


def _plat(type_plat="Pizza", nom="Margherita", prix=8.5):
    return {
        "Plat": type_plat,
        "Nom": nom,
        "Prix": prix,
        "Composition": {},
        "Recette": "margherita" if type_plat == "Pizza" else "",
    }


class TestMAJCommande:
    def test_cree_nouveau_fichier_si_aucune_commande(self, env_commandes):
        commandes, logs = env_commandes
        MAJ_commande(str(commandes), str(logs), _plat())
        fichiers = list(commandes.glob("commande_*.json"))
        assert len(fichiers) == 1

    def test_fichier_contient_informations(self, env_commandes):
        commandes, logs = env_commandes
        MAJ_commande(str(commandes), str(logs), _plat())
        f = next(commandes.glob("commande_*.json"))
        data = json.loads(f.read_text(encoding="utf-8"))
        assert "Informations" in data
        assert data["Informations"]["Statut"] == "En saisie"

    def test_fichier_contient_plat(self, env_commandes):
        commandes, logs = env_commandes
        MAJ_commande(str(commandes), str(logs), _plat("Pizza", "Margherita"))
        f = next(commandes.glob("commande_*.json"))
        data = json.loads(f.read_text(encoding="utf-8"))
        plats = list(data["Commande"].values())
        assert len(plats) == 1
        assert plats[0]["Plat"] == "Pizza"

    def test_ajoute_a_commande_existante(self, env_commandes):
        commandes, logs = env_commandes
        MAJ_commande(str(commandes), str(logs), _plat("Pizza"))
        MAJ_commande(str(commandes), str(logs), _plat("Grillade", "Poulet", 9.5))
        fichiers = list(commandes.glob("commande_*.json"))
        assert len(fichiers) == 1
        data = json.loads(fichiers[0].read_text(encoding="utf-8"))
        assert len(data["Commande"]) == 2

    def test_montant_calcule(self, env_commandes):
        commandes, logs = env_commandes
        MAJ_commande(str(commandes), str(logs), _plat("Pizza", prix=8.5))
        MAJ_commande(str(commandes), str(logs), _plat("Grillade", prix=9.5))
        f = next(commandes.glob("commande_*.json"))
        data = json.loads(f.read_text(encoding="utf-8"))
        assert data["Informations"]["Montant"] == pytest.approx(18.0)

    def test_plats_tries_par_type(self, env_commandes):
        commandes, logs = env_commandes
        MAJ_commande(str(commandes), str(logs), _plat("Grillade"))
        MAJ_commande(str(commandes), str(logs), _plat("Pizza"))
        f = next(commandes.glob("commande_*.json"))
        data = json.loads(f.read_text(encoding="utf-8"))
        cles = list(data["Commande"].keys())
        assert cles == sorted(cles, key=_sort_key_plat)

    def test_id_complet_dans_plat(self, env_commandes):
        commandes, logs = env_commandes
        MAJ_commande(str(commandes), str(logs), _plat("Pizza"))
        f = next(commandes.glob("commande_*.json"))
        data = json.loads(f.read_text(encoding="utf-8"))
        id_commande = data["Informations"]["ID"]
        plat = next(iter(data["Commande"].values()))
        assert plat["ID"].startswith(id_commande)
