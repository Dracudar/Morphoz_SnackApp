#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prep.py - Chargement des commandes en cours pour le poste de préparation

Description:
    Fournit la liste plate des plats actifs des commandes en cours, utilisée
    par le poste de préparation et l'affichage extérieur. Volontairement
    minimal (aucune dépendance vers carte/stock/impression) pour limiter la
    charge de l'application légère app_prep.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.16

Date de modification:
    2026.06.16
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.backend.config.chemins import get_command_root
from src.backend.config.persistance import _load_json_file


def get_live_orders_prep() -> List[Dict[str, Any]]:
    """Charge les plats actifs des commandes en cours, pour le poste de préparation.

    Retourne une liste plate (un dict par plat) avec composition complète, triée par ID de
    commande puis par ID de plat. Exclut les plats au statut Annulé et Livré.
    """
    root_folder = get_command_root()
    if root_folder is None:
        return []

    live_folder = None
    for folder_name in ("en_cours", "en-cours"):
        candidate = root_folder / folder_name
        if candidate.exists():
            live_folder = candidate
            break

    if live_folder is None:
        return []

    plats: List[Dict[str, Any]] = []
    for order_file in sorted(live_folder.glob("commande_*.json")):
        payload = _load_json_file(order_file)
        infos = payload.get("Informations", {})
        if not isinstance(infos, dict):
            infos = {}
        order_id = infos.get("ID", order_file.stem.replace("commande_", ""))
        command_lines = payload.get("Commande", {})
        if not isinstance(command_lines, dict):
            continue

        for line_key in sorted(command_lines.keys()):
            line_data = command_lines.get(line_key, {})
            if not isinstance(line_data, dict):
                continue

            status = str(line_data.get("Statut", "")).strip() or "Inconnu"
            if status.lower() in ("annulé", "livré", "non livré"):
                continue

            plats.append({
                "order_id": order_id,
                "file": order_file,
                "id": line_data.get("ID", line_key),
                "plat": line_data.get("Plat", ""),
                "nom": line_data.get("Nom", ""),
                "status": status,
                "composition": line_data.get("Composition", {}),
                "prix": line_data.get("Prix"),
                "prioritaire": bool(infos.get("Prioritaire", False)),
            })

    return plats
