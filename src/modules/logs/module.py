#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
module.py - Descripteur du module Journal

Auteur :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.11
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
