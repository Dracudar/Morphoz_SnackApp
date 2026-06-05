#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat pizza : ouvre l'interface de sélection de recette et de personnalisation.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.05.31

Date de modification:
    2026.06.05
"""

from typing import Dict, List, Optional

from PySide6.QtWidgets import QApplication, QDialog

from src.backend.data_sources import get_card_data, get_stock_data
from src.modules.plats.pizza.pizza_dialog import PizzaDialog


def route_selection(context, command_path: str) -> Optional[Dict]:
    """Ouvre le dialogue de personnalisation pizza et retourne les données du plat.

    Args:
        context: Context object (non utilisé dans le nouveau système).
        command_path: Chemin vers le fichier JSON de la commande en cours.

    Returns:
        Dict du plat (clés : Plat, Recette, Nom, Prix, Statut, Composition),
        ou None si l'utilisateur annule.
    """
    card_data = get_card_data()
    stock_data = get_stock_data()

    recettes = card_data.get("Pizza", {}).get("Recettes", {})
    if not recettes:
        return None

    bases = _get_available_bases(stock_data)
    stock_ingredients = _get_available_ingredients(stock_data)

    parent = QApplication.activeWindow()
    dialog = PizzaDialog(recettes, bases, stock_ingredients, parent=parent)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.result_data
    return None


# ── Helpers de préparation des données ────────────────────────────────────────

def _get_available_bases(stock_data: Dict) -> List[str]:
    """Retourne les bases pizza disponibles (non hors-stock) depuis le stock."""
    bases_dict = stock_data.get("Plats", {}).get("Pizza", {}).get("Bases", {})
    if not isinstance(bases_dict, dict):
        return []
    return [
        name for name, data in bases_dict.items()
        if isinstance(data, dict) and not data.get("OutOfStock", False)
    ]


def _get_available_ingredients(stock_data: Dict) -> Dict[str, List[str]]:
    """Retourne les ingrédients disponibles par catégorie (sans Pâtes, sans hors-stock)."""
    ingr_dict = stock_data.get("Ingrédients", {})
    if not isinstance(ingr_dict, dict):
        return {}

    result = {}
    for cat, items in ingr_dict.items():
        if cat == "Pâtes" or not isinstance(items, dict):
            continue
        available = [
            name for name, data in items.items()
            if isinstance(data, dict) and not data.get("OutOfStock", False)
        ]
        if available:
            result[cat] = available
    return result
