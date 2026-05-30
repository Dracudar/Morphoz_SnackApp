#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interface_principale.py - Vue principale de l'interface

Description:
    Assemble la saisie dynamique et le suivi des commandes dans la fenetre principale.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.20

Date de modification:
    2026.05.30
"""

from __future__ import annotations

from src.modules.commandes_saisie.backend.commandes_saisie_save import ajouter_portion_frites


LABEL = "Frites"
TOOLTIP = "Ajouter une portion de frites a la commande en cours"


def execute(context=None):
    result = ajouter_portion_frites()
    if not result.get("ok"):
        return {
            "ok": False,
            "message": "Impossible d'ajouter la portion de frites.",
            "result": result,
        }

    return {
        "ok": True,
        "message": f"Portion de frites ajoutee a la commande {result.get('order_id', '')}.",
        "result": result,
    }


def get_module_descriptor():
    return {
        "label": LABEL,
        "tooltip": TOOLTIP,
        "action": execute,
        "enabled": True,
    }
