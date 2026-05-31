"""Grillade plat handler - opens UI with meat quantity limits."""

from typing import Dict, Optional


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
        Item data dict with plat, nom, composition, prix, or None if cancelled
    """
    # TODO: Import and open grillade UI dialog
    # For now, return placeholder
    return {
        "plat": "Grillade",
        "nom": "Grillade Mixte",
        "prix": 12.00,
        "statut": "En attente",
        "composition": {},
    }
