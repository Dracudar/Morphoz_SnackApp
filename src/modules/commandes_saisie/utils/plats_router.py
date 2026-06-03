#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plats_router.py

Description:
    Orchestrateur de routage vers les handlers de plats par catégorie : chaque catégorie expose une fonction route_selection() dans son rooting.py.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.31

Date de modification:
    2026.05.31
"""

import importlib
from typing import Optional, Dict


PLAT_HANDLERS = {
    "Pizza": "src.modules.plats.pizza.rooting",
    "Grillade": "src.modules.plats.grillade.rooting",
    "Frites": "src.modules.plats.frites.rooting",
    "Salade composée": "src.modules.plats.salade_composee.rooting",
}


def route_plat_selection(plat_name: str, context, command_path: str) -> Optional[Dict]:
    """Dispatch plat selection to appropriate handler.

    Each plat's rooting.py module has a uniform route_selection() function.
    Only the module path varies based on plat_name.

    Args:
        plat_name: Category name (e.g., "Pizza", "Frites")
        context: Context object (can be None)
        command_path: Path to current order file (string)

    Returns:
        Item data dict to add to order, or None if cancelled/error
    """
    if plat_name not in PLAT_HANDLERS:
        print(f"Unknown plat: {plat_name}")
        return None

    module_path = PLAT_HANDLERS[plat_name]
    try:
        module = importlib.import_module(module_path)
        return module.route_selection(context, command_path)
    except Exception as e:
        print(f"Error routing plat {plat_name}: {e}")
        return None

