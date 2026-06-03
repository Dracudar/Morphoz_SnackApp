#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat frites : ajout direct à la commande sans dialogue de personnalisation.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.31

Date de modification:
    2026.05.31
"""

from typing import Dict
from src.backend.data_sources import get_card_data


def route_selection(context, command_path: str) -> Dict:
    """Route frites selection - direct add without dialog.

    Frites don't need personalization, so we just add a standard portion
    directly to the order.

    Args:
        context: Context object (unused)
        command_path: Path to current order file (unused)

    Returns:
        Item data dict with Plat, Nom, Prix, Composition (uppercase keys)
    """
    card_data = get_card_data()
    prix = card_data.get("Frites", {}).get("Prix", 3.50)

    return {
        "Plat": "Frites",
        "Nom": "Portion frites",
        "Prix": prix,
        "Statut": "En attente",
        "Composition": [],
    }
