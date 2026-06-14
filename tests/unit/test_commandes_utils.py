"""
Tests unitaires pour src/backend/commandes_utils.py.
"""

import json
import os
import pytest
from datetime import datetime

from src.backend.commandes_utils import (
    DerniersIDCache,
    PREFIXES_PLAT,
    charger_fichier_commande,
    plats_identiques,
)


def _today():
    return datetime.now().strftime("%Y%m%d")


# ── DerniersIDCache ───────────────────────────────────────────────────────────

class TestDerniersIDCacheInit:
    def test_init_vide_compteurs_a_zero(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 0
        for cle in PREFIXES_PLAT:
            assert cache._data[cle] == 0

    def test_init_depuis_fichier_existant(self, tmp_path):
        today = _today()
        data = {today: {"commande": 5, "pizza": 3, "grillade": 1,
                        "frites": 0, "salade composée": 0, "crêpe": 0}}
        (tmp_path / "derniers_ID.json").write_text(json.dumps(data), encoding="utf-8")
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 5
        assert cache._data["pizza"] == 3

    def test_init_migration_ancien_format_entier(self, tmp_path):
        today = _today()
        data = {today: 8}
        (tmp_path / "derniers_ID.json").write_text(json.dumps(data), encoding="utf-8")
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 8

    def test_init_depuis_ancien_nom_fichier(self, tmp_path):
        today = _today()
        data = {today: {"commande": 4, "pizza": 0, "grillade": 0,
                        "frites": 0, "salade composée": 0, "crêpe": 0}}
        (tmp_path / "dernier_id.json").write_text(json.dumps(data), encoding="utf-8")
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 4

    def test_init_autre_jour_ignore(self, tmp_path):
        data = {"20200101": {"commande": 99, "pizza": 0, "grillade": 0,
                             "frites": 0, "salade composée": 0, "crêpe": 0}}
        (tmp_path / "derniers_ID.json").write_text(json.dumps(data), encoding="utf-8")
        cache = DerniersIDCache(str(tmp_path))
        assert cache._data["commande"] == 0


class TestProchainIdCommande:
    def test_format_aaaammjj_tiret_000(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_commande()
        today = _today()
        assert id_ == f"{today}-001"

    def test_incremente_a_chaque_appel(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_commande()
        id2 = cache.prochain_id_commande()
        assert id2 == f"{_today()}-002"

    def test_persiste_apres_rechargement(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_commande()
        cache.prochain_id_commande()
        cache2 = DerniersIDCache(str(tmp_path))
        assert cache2._data["commande"] == 2


class TestDecrementerCommande:
    def test_decremente(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_commande()
        cache.decrementer_commande()
        assert cache._data["commande"] == 0

    def test_pas_en_dessous_de_zero(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.decrementer_commande()
        assert cache._data["commande"] == 0


class TestProchainIdPlat:
    @pytest.mark.parametrize("type_plat, prefixe_attendu", [
        ("pizza", "P"),
        ("grillade", "G"),
        ("frites", "F"),
        ("salade composée", "S"),
        ("crêpe", "C"),
    ])
    def test_prefixe_par_type(self, tmp_path, type_plat, prefixe_attendu):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_plat(type_plat)
        assert id_[0] == prefixe_attendu

    def test_format_lettre_trois_chiffres(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_plat("pizza")
        assert id_ == "P001"

    def test_incremente_independamment_par_type(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_plat("pizza")
        cache.prochain_id_plat("pizza")
        id_g = cache.prochain_id_plat("grillade")
        assert id_g == "G001"

    def test_type_inconnu_prefixe_x(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_plat("boisson")
        assert id_.startswith("X")

    def test_insensible_a_la_casse(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        id_ = cache.prochain_id_plat("Pizza")
        assert id_ == "P001"


class TestDecrementerPlat:
    def test_decremente_si_dernier(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_plat("pizza")  # P001
        cache.decrementer_plat("pizza", "P001")
        assert cache._data["pizza"] == 0

    def test_ne_decremente_pas_si_pas_dernier(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_plat("pizza")  # P001
        cache.prochain_id_plat("pizza")  # P002
        cache.decrementer_plat("pizza", "P001")  # pas le dernier
        assert cache._data["pizza"] == 2

    def test_ignore_id_invalide(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.prochain_id_plat("pizza")
        cache.decrementer_plat("pizza", "invalide")
        assert cache._data["pizza"] == 1

    def test_pas_en_dessous_de_zero(self, tmp_path):
        cache = DerniersIDCache(str(tmp_path))
        cache.decrementer_plat("pizza", "P001")
        assert cache._data["pizza"] == 0


# ── plats_identiques ──────────────────────────────────────────────────────────

class TestPlatsIdentiques:
    def _plat(self, **kwargs):
        base = {"Plat": "Pizza", "Recette": "Margherita",
                "Nom": "Margherita", "Composition": {"tomate": 1}}
        base.update(kwargs)
        return base

    def test_identiques(self):
        plat = self._plat()
        assert plats_identiques(plat, plat.copy()) is True

    def test_type_different(self):
        a = self._plat(Plat="Pizza")
        b = self._plat(Plat="Grillade")
        assert plats_identiques(a, b) is False

    def test_recette_differente(self):
        a = self._plat(Recette="Margherita")
        b = self._plat(Recette="4 Fromages")
        assert plats_identiques(a, b) is False

    def test_nom_different(self):
        a = self._plat(Nom="A")
        b = self._plat(Nom="B")
        assert plats_identiques(a, b) is False

    def test_composition_differente(self):
        a = self._plat(Composition={"tomate": 1})
        b = self._plat(Composition={"tomate": 2})
        assert plats_identiques(a, b) is False

    def test_composition_identique_ordre_different(self):
        a = self._plat(Composition={"tomate": 1, "mozzarella": 2})
        b = self._plat(Composition={"mozzarella": 2, "tomate": 1})
        assert plats_identiques(a, b) is True


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
