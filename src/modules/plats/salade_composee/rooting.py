"""Salade composée plat handler - opens ingredient selector."""

from typing import Dict, Optional


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
        Item data dict with plat, nom, composition, prix, or None if cancelled
    """
    # TODO: Import and open salad ingredient selector dialog
    # For now, return placeholder
    return {
        "plat": "Salade composée",
        "nom": "Salade Verte",
        "prix": 7.50,
        "statut": "En attente",
        "composition": {},
    }
