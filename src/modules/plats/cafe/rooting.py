#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Rooteur café : ajout direct à la commande sans dialogue de personnalisation.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.15

Date de modification:
    2026.06.15
"""

from typing import Dict, Optional
from src.backend.data_sources import get_card_data


def route_selection(context, command_path: str) -> Optional[Dict]:
    """Route café selection - direct add without dialog.

    Café don't need personalization, so we just add a standard cup
    directly to the order. Returns None if café is out of stock.

    Args:
        context: Context object (unused)
        command_path: Path to current order file (unused)

    Returns:
        Item data dict with Plat, Nom, Prix, Composition, or None if out of stock.
    """

    card_data = get_card_data()
    prix = card_data.get("Café", {}).get("Prix", 1.0)

    return {
        "Plat": "Café",
        "Nom": "Café",
        "Prix": prix,
        "Statut": "En attente",
        "Composition": [],
    }
