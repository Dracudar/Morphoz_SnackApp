#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conftest.py - Fixtures et configuration partagées pour les tests

Description:
    Fixtures Pytest partagées entre tous les tests : réinitialisation des
    singletons, jeux de données temporaires et contexte d'environnement.

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
import src.backend.commandes_utils as commandes_utils
import src.backend.data.stock as stock_module
import src.backend.logger as logger_module


@pytest.fixture(autouse=True)
def reset_singletons():
    """Réinitialise les singletons entre chaque test."""
    commandes_utils._id_cache = None
    stock_module._stock_cache_instance = None
    logger_module._log_index = 0
    logger_module._log_index_date = ""
    yield
    commandes_utils._id_cache = None
    stock_module._stock_cache_instance = None
    logger_module._log_index = 0
    logger_module._log_index_date = ""


@pytest.fixture
def stock_data():
    return {
        "Plats": {
            "Pizza": {
                "Pâte à pizza": {"Quantité": 10, "OutOfStock": False}
            },
            "Grillades": {
                "Poulet": {"Quantité": 5, "OutOfStock": False},
                "Entrecôte": {"Quantité": 0, "OutOfStock": True},
            },
        }
    }


@pytest.fixture
def stock_file(tmp_path, stock_data):
    f = tmp_path / "stock.json"
    f.write_text(json.dumps(stock_data), encoding="utf-8")
    return f


@pytest.fixture
def commandes_dir(tmp_path):
    commandes = tmp_path / "commandes"
    commandes.mkdir()
    (commandes / "en_cours").mkdir()
    (commandes / "terminee").mkdir()
    (commandes / "annulee").mkdir()
    (commandes / "corrompu").mkdir()
    return commandes


@pytest.fixture
def logs_dir(tmp_path):
    d = tmp_path / "logs"
    d.mkdir()
    return d


@pytest.fixture
def id_cache(tmp_path, logs_dir):
    """Cache d'IDs journaliers pointant sur un répertoire temporaire."""
    from src.backend.commandes_utils import DerniersIDCache
    cache = DerniersIDCache(str(logs_dir))
    commandes_utils._id_cache = cache
    return cache


@pytest.fixture
def mock_logger(monkeypatch):
    """Remplace logger.log par une fonction muette."""
    monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
