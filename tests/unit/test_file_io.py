#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_file_io.py - Tests unitaires pour le cache de lecture mtime et les signatures

Description:
    Tests unitaires pour src/backend/file_io.py : cache de lecture indexé sur
    (mtime, taille), signatures de fichier/dossier et élagage du cache.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.27
"""

import json
import os

import pytest

from src.backend import file_io


@pytest.fixture(autouse=True)
def _cache_propre():
    """Garantit un cache de lecture vierge avant et après chaque test."""
    file_io.vider_cache_lecture()
    yield
    file_io.vider_cache_lecture()


def _ecrire(chemin, payload):
    chemin.write_text(json.dumps(payload), encoding="utf-8")


# ── charger_json_cache ────────────────────────────────────────────────────────

class TestChargerJsonCache:
    def test_charge_le_contenu(self, tmp_path):
        f = tmp_path / "data.json"
        _ecrire(f, {"a": 1})
        assert file_io.charger_json_cache(f) == {"a": 1}

    def test_fichier_absent_renvoie_dict_vide(self, tmp_path):
        assert file_io.charger_json_cache(tmp_path / "absent.json") == {}

    def test_ne_reparse_pas_si_inchange(self, tmp_path, monkeypatch):
        f = tmp_path / "data.json"
        _ecrire(f, {"a": 1})

        appels = {"n": 0}
        vrai_charger = file_io.charger_json

        def compteur(chemin):
            appels["n"] += 1
            return vrai_charger(chemin)

        monkeypatch.setattr(file_io, "charger_json", compteur)

        file_io.charger_json_cache(f)
        file_io.charger_json_cache(f)
        file_io.charger_json_cache(f)
        assert appels["n"] == 1  # une seule lecture disque malgré 3 appels

    def test_relit_apres_modification(self, tmp_path):
        f = tmp_path / "data.json"
        _ecrire(f, {"a": 1})
        assert file_io.charger_json_cache(f) == {"a": 1}

        _ecrire(f, {"a": 2, "b": 3})  # contenu et taille différents
        os.utime(f, ns=(2_000_000_000, 2_000_000_000))  # mtime distinct, robustesse
        assert file_io.charger_json_cache(f) == {"a": 2, "b": 3}

    def test_fichier_supprime_purge_l_entree(self, tmp_path):
        f = tmp_path / "data.json"
        _ecrire(f, {"a": 1})
        file_io.charger_json_cache(f)
        f.unlink()
        assert file_io.charger_json_cache(f) == {}
        assert str(f) not in file_io._cache_lecture


# ── signature_fichier ─────────────────────────────────────────────────────────

class TestSignatureFichier:
    def test_none_si_absent(self, tmp_path):
        assert file_io.signature_fichier(tmp_path / "absent.json") is None

    def test_change_apres_modification(self, tmp_path):
        f = tmp_path / "data.json"
        _ecrire(f, {"a": 1})
        sig1 = file_io.signature_fichier(f)
        _ecrire(f, {"a": 22})
        os.utime(f, ns=(3_000_000_000, 3_000_000_000))
        assert file_io.signature_fichier(f) != sig1


# ── signature_dossier ─────────────────────────────────────────────────────────

class TestSignatureDossier:
    def test_dossier_absent_renvoie_tuple_vide(self, tmp_path):
        assert file_io.signature_dossier(tmp_path / "absent") == ()

    def test_reflete_ajout_et_suppression(self, tmp_path):
        _ecrire(tmp_path / "commande_1.json", {})
        sig1 = file_io.signature_dossier(tmp_path)
        assert len(sig1) == 1

        _ecrire(tmp_path / "commande_2.json", {})
        sig2 = file_io.signature_dossier(tmp_path)
        assert len(sig2) == 2 and sig2 != sig1

        (tmp_path / "commande_1.json").unlink()
        sig3 = file_io.signature_dossier(tmp_path)
        assert len(sig3) == 1 and sig3 != sig2

    def test_ignore_les_fichiers_hors_motif(self, tmp_path):
        _ecrire(tmp_path / "commande_1.json", {})
        _ecrire(tmp_path / "autre.txt", {})
        assert len(file_io.signature_dossier(tmp_path)) == 1

    def test_change_apres_modification_contenu(self, tmp_path):
        f = tmp_path / "commande_1.json"
        _ecrire(f, {"a": 1})
        sig1 = file_io.signature_dossier(tmp_path)
        _ecrire(f, {"a": 2})
        os.utime(f, ns=(4_000_000_000, 4_000_000_000))
        assert file_io.signature_dossier(tmp_path) != sig1


# ── elaguer_cache_dossier ─────────────────────────────────────────────────────

class TestElaguerCacheDossier:
    def test_retire_les_entrees_disparues(self, tmp_path):
        f1 = tmp_path / "commande_1.json"
        f2 = tmp_path / "commande_2.json"
        _ecrire(f1, {})
        _ecrire(f2, {})
        file_io.charger_json_cache(f1)
        file_io.charger_json_cache(f2)

        # f1 n'est plus présent : seul f2 doit rester en cache
        file_io.elaguer_cache_dossier(tmp_path, ["commande_2.json"])
        assert str(f1) not in file_io._cache_lecture
        assert str(f2) in file_io._cache_lecture

    def test_n_affecte_pas_un_autre_dossier(self, tmp_path):
        autre = tmp_path / "autre"
        autre.mkdir()
        f = autre / "commande_9.json"
        _ecrire(f, {})
        file_io.charger_json_cache(f)
        # On élague tmp_path (vide) : l'entrée du sous-dossier ne doit pas être touchée
        file_io.elaguer_cache_dossier(tmp_path, [])
        assert str(f) in file_io._cache_lecture


# ── vider_cache_lecture ───────────────────────────────────────────────────────

class TestViderCacheLecture:
    def test_vide_tout(self, tmp_path):
        f = tmp_path / "data.json"
        _ecrire(f, {"a": 1})
        file_io.charger_json_cache(f)
        assert file_io._cache_lecture
        file_io.vider_cache_lecture()
        assert not file_io._cache_lecture
