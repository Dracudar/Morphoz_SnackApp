"""Frites plat handler - direct add (no UI dialog)."""

from typing import Dict


def route_selection(context, command_path: str) -> Dict:
    """Route frites selection - direct add without dialog.

    Frites don't need personalization, so we just add a standard portion
    directly to the order.

    Args:
        context: Context object (unused)
        command_path: Path to current order file (unused)

    Returns:
        Item data dict with plat, nom, prix
    """
    # Standard frites portion - no dialog needed
    return {
        "plat": "Frites",
        "nom": "Portion Standard",
        "prix": 3.50,
        "statut": "En attente",
        "composition": {},
    }
