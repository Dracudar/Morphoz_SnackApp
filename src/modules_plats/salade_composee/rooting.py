#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat salade composée : ouvre le sélecteur d'ingrédients.

Author :
    Dracudar

Version:
    1.3

Date de création :
    2026.05.31

Date de modification:
    2026.06.06
"""

from typing import Dict, List, Optional

from PySide6.QtWidgets import QApplication, QDialog

from src.backend.data.carte import get_card_data
from src.backend.data.stock import get_stock_cache
from src.modules_plats.salade_composee.salade_dialog import SaladeDialog


def route_selection(context, command_path: str) -> Optional[Dict]:
    """Ouvre le dialogue de personnalisation salade et retourne les données du plat.

    Args:
        context: Context object (non utilisé dans le nouveau système).
        command_path: Chemin vers le fichier JSON de la commande en cours.

    Returns:
        Dict du plat (clés : Plat, Nom, Prix, Statut, Composition),
        ou None si l'utilisateur annule.
    """
    card_data = get_card_data()
    stock_data = get_stock_cache().data

    prix = card_data.get("Salade composée", {}).get("Prix", 5.0)
    stock_ingredients = _get_available_ingredients(stock_data)

    parent = QApplication.activeWindow()
    dialog = SaladeDialog(prix, stock_ingredients, parent=parent)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.result_data
    return None


# ── Helpers de préparation des données ────────────────────────────────────────

def _items_disponibles(items_dict: Dict) -> List[str]:
    """Retourne les noms des articles non hors-stock depuis un dict {nom: {OutOfStock: bool}}."""
    return [
        name for name, data in items_dict.items()
        if isinstance(data, dict) and not data.get("OutOfStock", False)
    ]


def _get_available_ingredients(stock_data: Dict) -> Dict[str, List[str]]:
    """Retourne les ingrédients disponibles par catégorie pour la salade composée.

    Combine les ingrédients communs (Ingrédients) et les pâtes propres à la salade
    (Plats > Salade composée > Pâtes).
    """
    result = {}

    # Pâtes : déplacées dans la section salade du stock
    pates_dict = stock_data.get("Plats", {}).get("Salade composée", {}).get("Pâtes", {})
    if isinstance(pates_dict, dict):
        disponibles = _items_disponibles(pates_dict)
        if disponibles:
            result["Pâtes"] = disponibles

    # Ingrédients communs (Viande, Fromage, Fruits et légumes, Herbes…)
    ingr_dict = stock_data.get("Ingrédients", {})
    if isinstance(ingr_dict, dict):
        for cat, items in ingr_dict.items():
            if not isinstance(items, dict):
                continue
            disponibles = _items_disponibles(items)
            if disponibles:
                result[cat] = disponibles

    return result
