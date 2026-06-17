#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
module.py - Descripteur du module Journal

Description:
    Descripteur du module Journal pour le registre dynamique des modules UI.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.11

Date de modification:
    2026.06.14
"""

from __future__ import annotations


def get_module_descriptor() -> dict:
    """Retourne le descripteur du module Journal pour le registre UI."""
    return {
        "label":     "Journal",
        "icon_path": "src/modules/logs/icon.svg",
        "tooltip":   "Consulter le journal des événements applicatifs",
        "enabled":   True,
    }
