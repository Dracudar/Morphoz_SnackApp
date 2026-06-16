#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat crêpe : ouvre l'interface de sélection des garnitures.

Author :
    Dracudar

Version:
    1.2

Date de création :
    2026.06.06

Date de modification:
    2026.06.06
"""

from typing import Dict, Optional

from PySide6.QtWidgets import QApplication, QDialog

from src.backend.data_sources import get_card_data, get_stock_cache
from src.modules_plats.crepe.crepe_dialog import CrepeDialog


def route_selection(context, command_path: str) -> Optional[Dict]:
    """Ouvre le dialogue de personnalisation crêpe et retourne les données du plat.

    Args:
        context: Context object (non utilisé dans le nouveau système).
        command_path: Chemin vers le fichier JSON de la commande en cours.

    Returns:
        Dict du plat (clés : Plat, Nom, Prix, Statut, Composition),
        ou None si l'utilisateur annule.
    """
    card_data = get_card_data()
    stock_data = get_stock_cache().data

    crepe_data = card_data.get("Crêpe", {})
    prix_base = crepe_data.get("Prix", 1.5)
    garnitures = _get_available_garnitures(crepe_data, stock_data)

    parent = QApplication.activeWindow()
    dialog = CrepeDialog(prix_base, garnitures, parent=parent)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.result_data
    return None


# ── Helpers de préparation des données ────────────────────────────────────────

def _build_ingredient_availability(stock_data: Dict) -> Dict[str, bool]:
    """Construit un dict {nom_ingrédient: disponible} par scan récursif du stock.

    Si un ingrédient n'est pas trouvé dans le stock, il est considéré disponible
    par défaut pour éviter de bloquer les garnitures non encore référencées.
    """
    availability: Dict[str, bool] = {}

    def _scan(node: Dict):
        for nom, data in node.items():
            if not isinstance(data, dict):
                continue
            if "OutOfStock" in data:
                availability[nom] = not data["OutOfStock"]
            else:
                _scan(data)

    _scan(stock_data)
    return availability


def _get_available_garnitures(crepe_data: Dict, stock_data: Dict) -> Dict[str, float]:
    """Retourne les garnitures disponibles (non hors-stock) avec leur prix.

    Une garniture est disponible si tous ses ingrédients (listés dans la carte)
    sont disponibles dans le stock. Les ingrédients absents du stock sont ignorés.
    """
    garnitures_carte = crepe_data.get("Garnitures", {})
    availability = _build_ingredient_availability(stock_data)

    result = {}
    for nom, data in garnitures_carte.items():
        if data.get("Etat") in ("Hors stock", "Retiré", "Archivé"):
            continue
        ingredients = data.get("Ingrédients", [])
        if all(availability.get(ingr, True) for ingr in ingredients):
            result[nom] = data.get("Prix", 0.0)

    return result
