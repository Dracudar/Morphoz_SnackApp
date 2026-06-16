#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_impression.py - Tests unitaires pour Impression

Description:
    Tests unitaires pour src/backend/config/impression.py.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.12

Date de modification:
    2026.06.16
"""

import pytest

from src.backend.config.impression import get_print_options


# ── get_print_options ─────────────────────────────────────────────────────────

class TestGetPrintOptions:
    def test_defauts_si_config_vide(self, monkeypatch):
        monkeypatch.setattr("src.backend.config.persistance._load_app_config", lambda: {})
        opts = get_print_options()
        assert opts["impression_active"] is True
        assert opts["ticket_client"] is True
        assert opts["ticket_cuisine"] is True

    def test_valeurs_personnalisees(self, monkeypatch):
        monkeypatch.setattr("src.backend.config.persistance._load_app_config", lambda: {
            "impression": {
                "impression_active": False,
                "ticket_client": True,
                "ticket_cuisine": False,
            }
        })
        opts = get_print_options()
        assert opts["impression_active"] is False
        assert opts["ticket_client"] is True
        assert opts["ticket_cuisine"] is False
