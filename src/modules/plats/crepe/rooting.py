#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat crêpe : ouvre l'interface de sélection des garnitures.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.06

Date de modification:
    2026.06.06
"""

from typing import Dict, Optional

from PySide6.QtWidgets import QApplication, QDialog

from src.backend.data_sources import get_card_data, get_stock_data
from src.modules.plats.crepe.crepe_dialog import CrepeDialog


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
    stock_data = get_stock_data()

    crepe_data = card_data.get("Crêpe", {})
    prix_base = crepe_data.get("Prix", 1.5)
    garnitures = _get_available_garnitures(crepe_data, stock_data)

    parent = QApplication.activeWindow()
    dialog = CrepeDialog(prix_base, garnitures, parent=parent)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.result_data
    return None


# ── Helpers de préparation des données ────────────────────────────────────────

def _get_available_garnitures(crepe_data: Dict, stock_data: Dict) -> Dict[str, float]:
    """Retourne les garnitures disponibles (non hors-stock) avec leur prix.

    Croise les garnitures de la carte active avec l'état du stock.
    """
    garnitures_carte = crepe_data.get("Garnitures", {})
    garnitures_stock = stock_data.get("Plats", {}).get("Crêpe", {}).get("Garnitures", {})

    result = {}
    for nom, data in garnitures_carte.items():
        if data.get("Etat") in ("Hors stock", "Retiré", "Archivé"):
            continue
        stock_entry = garnitures_stock.get(nom, {})
        if stock_entry.get("OutOfStock", False):
            continue
        result[nom] = data.get("Prix", 0.0)

    return result
