#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat salade composée : ouvre le sélecteur d'ingrédients.

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
    """Route salade composée selection flow.

    Opens UI dialog for:
    1. Base salad selection
    2. Ingredient picker (check which ingredients to include)
    3. Dressing selection

    Args:
        context: Context object (unused for now)
        command_path: Path to current order file

    Returns:
        Item data dict with Plat, Nom, Composition, Prix (uppercase keys), or None if cancelled
    """
    card_data = get_card_data()
    prix = card_data.get("Salade composée", {}).get("Prix", 7.50)

    # TODO: Import and open salad ingredient selector dialog
    # For now, return placeholder
    return {
        "Plat": "Salade composée",
        "Nom": "Salade Verte",
        "Prix": prix,
        "Statut": "En attente",
        "Composition": {},
    }
