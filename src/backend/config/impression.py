#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
impression.py - Options d'activation de l'impression

Description:
    Lecture des options d'impression (globale, ticket client, ticket cuisine)
    depuis la configuration applicative (assets/config.json).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.16

Date de modification:
    2026.06.16
"""

from __future__ import annotations

from typing import Dict


def get_print_options() -> Dict[str, bool]:
    """Retourne les options d'activation de l'impression (globale, ticket client et cuisine)."""
    from src.backend.config.persistance import _load_app_config

    config = _load_app_config()
    impression = config.get("impression", {})
    return {
        "impression_active": bool(impression.get("impression_active", True)),
        "ticket_client": bool(impression.get("ticket_client", True)),
        "ticket_cuisine": bool(impression.get("ticket_cuisine", True)),
    }
