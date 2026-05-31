"""Pizza plat handler - opens UI for recipe selection and personalization."""

from typing import Dict, Optional


def route_selection(context, command_path: str) -> Optional[Dict]:
    """Route pizza selection flow.

    Opens UI dialog for:
    1. Recipe selection (Margherita, 4 Fromages, etc.)
    2. Personalization (size, crust, toppings)

    Args:
        context: Context object (unused for now)
        command_path: Path to current order file

    Returns:
        Item data dict with plat, nom, composition, prix, or None if cancelled
    """
    # TODO: Import and open pizza UI dialog
    # For now, return placeholder
    return {
        "plat": "Pizza",
        "nom": "Margherita",
        "prix": 10.00,
        "statut": "En attente",
        "composition": {},
    }
