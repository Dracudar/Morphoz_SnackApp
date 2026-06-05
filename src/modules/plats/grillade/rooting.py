#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rooting.py

Description:
    Handler du plat grillade : ouvre l'interface de sélection avec limites de quantité de viande.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.05.31

Date de modification:
    2026.06.06
"""

from typing import Dict, Optional

from PySide6.QtWidgets import QApplication, QDialog

from src.backend.data_sources import get_card_data, get_stock_data
from src.modules.plats.grillade.grillade_dialog import GrilladeDialog


def route_selection(context, command_path: str) -> Optional[Dict]:
    """Ouvre le dialogue de personnalisation grillade et retourne les données du plat.

    Args:
        context: Context object (non utilisé dans le nouveau système).
        command_path: Chemin vers le fichier JSON de la commande en cours.

    Returns:
        Dict du plat (clés : Plat, Nom, Prix, Statut, Composition),
        ou None si l'utilisateur annule.
    """
    card_data = get_card_data()
    stock_data = get_stock_data()

    prix = card_data.get("Grillade", {}).get("Prix", 6.5)
    grillades_stock = _get_available_grillades(stock_data)

    if not grillades_stock:
        return None

    parent = QApplication.activeWindow()
    dialog = GrilladeDialog(prix, grillades_stock, parent=parent)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.result_data
    return None


# ── Helpers de préparation des données ────────────────────────────────────────

def _get_available_grillades(stock_data: Dict) -> Dict[str, Dict]:
    """Retourne les grillades depuis le stock (y compris hors-stock pour affichage grisé)."""
    grillades = stock_data.get("Plats", {}).get("Grillades", {})
    if not isinstance(grillades, dict):
        return {}
    return grillades
