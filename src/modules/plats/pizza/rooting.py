#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat pizza : ouvre l'interface de sélection de recette et de personnalisation.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.31

Date de modification:
    2026.05.31
"""

from typing import Dict, Optional
from src.backend.data_sources import get_card_data


def route_selection(context, command_path: str) -> Optional[Dict]:
    """Route pizza selection flow.

    Opens UI dialog for:
    1. Recipe selection (Margherita, 4 Fromages, etc.)
    2. Personalization (size, crust, toppings)

    Args:
        context: Context object (unused for now)
        command_path: Path to current order file

    Returns:
        Item data dict with Plat, Nom, Composition, Prix (uppercase keys), or None if cancelled
    """
    card_data = get_card_data()
    prix = card_data.get("Pizza", {}).get("Prix", 10.00)

    # TODO: Import and open pizza UI dialog
    # For now, return placeholder
    return {
        "Plat": "Pizza",
        "Nom": "Margherita",
        "Prix": prix,
        "Statut": "En attente",
        "Composition": {},
    }
