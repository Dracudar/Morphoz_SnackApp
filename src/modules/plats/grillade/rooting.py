#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat grillade : ouvre l'interface de sélection avec limites de quantité de viande.

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
    """Route grillade selection flow.

    Opens UI dialog for:
    1. Meat selection (poulet, boeuf, etc.)
    2. Quantity limits (specific rules for grillade)
    3. Side selections (fries, salad, etc.)

    Args:
        context: Context object (unused for now)
        command_path: Path to current order file

    Returns:
        Item data dict with Plat, Nom, Composition, Prix (uppercase keys), or None if cancelled
    """
    card_data = get_card_data()
    prix = card_data.get("Grillade", {}).get("Prix", 12.00)

    # TODO: Import and open grillade UI dialog
    # For now, return placeholder
    return {
        "Plat": "Grillade",
        "Nom": "Grillade Mixte",
        "Prix": prix,
        "Statut": "En attente",
        "Composition": {},
    }
