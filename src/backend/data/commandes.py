#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
commandes.py - Chargement des commandes (brouillons, en cours, historique)

Description:
    Lecture et structuration des fichiers JSON de commandes pour les vues
    de saisie, de suivi en temps réel et d'historique.

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

import os
from pathlib import Path
from typing import Any, Dict, List

from src.backend.config.chemins import get_command_root
from src.backend.config.persistance import _load_json_file


def _parse_order_file(order_file: Path) -> Dict[str, Any]:
    """Charge et structure le contenu d'un fichier de commande JSON."""
    payload = _load_json_file(order_file)
    infos = payload.get("Informations", {})
    if not isinstance(infos, dict):
        infos = {}
    command_lines = payload.get("Commande", {})
    if not isinstance(command_lines, dict):
        command_lines = {}
    return infos, command_lines


def get_draft_orders() -> List[Dict[str, Any]]:
    """Charge les commandes en brouillon (en cours de saisie) depuis le dossier racine des commandes. Maximum 1 brouillon actif à la fois."""
    root_folder = get_command_root()
    if root_folder is None:
        return []

    if not root_folder.exists():
        return []

    orders: List[Dict[str, Any]] = []
    # Only search in root folder, not in subdirectories
    files = [root_folder / f for f in os.listdir(str(root_folder)) if f.startswith("commande_") and f.endswith(".json")]

    for order_file in sorted(files):
        infos, command_lines = _parse_order_file(order_file)

        items: List[Dict[str, Any]] = []
        for line_key in sorted(command_lines.keys()):
            line_data = command_lines.get(line_key, {})
            if not isinstance(line_data, dict):
                continue

            status = str(line_data.get("Statut", "")).strip() or "Inconnu"
            if status.lower() == "annulé":
                status = "Annulé"

            items.append(
                {
                    "id": line_data.get("ID", line_key),
                    "plat": line_data.get("Plat", ""),
                    "nom": line_data.get("Nom", ""),
                    "status": status,
                    "price": line_data.get("Prix"),
                }
            )

        active_items = [item for item in items if item["status"].lower() != "annulé"]

        orders.append(
            {
                "file": order_file,
                "id": infos.get("ID", order_file.stem.replace("commande_", "")),
                "status": infos.get("Statut", ""),
                "created_at": infos.get("Date de création", ["", ""]),
                "items": active_items,
                "amount": infos.get("Montant", 0),
                "priority": bool(infos.get("Prioritaire", False)),
            }
        )

    return orders


def get_live_orders() -> List[Dict[str, Any]]:
    """Charge les commandes en cours depuis le sous-dossier `en_cours` du dossier de commandes."""
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

    orders: List[Dict[str, Any]] = []
    for order_file in sorted(live_folder.glob("commande_*.json")):
        infos, command_lines = _parse_order_file(order_file)

        items: List[Dict[str, Any]] = []
        delivered_count = 0
        cancelled_count = 0

        for line_key in sorted(command_lines.keys()):
            line_data = command_lines.get(line_key, {})
            if not isinstance(line_data, dict):
                continue

            status = str(line_data.get("Statut", "")).strip() or "Inconnu"
            if status.lower() == "annule":
                status = "Annule"
            if status.lower() == "livré":
                delivered_count += 1
            elif status.lower() == "annulé":
                cancelled_count += 1

            items.append(
                {
                    "id": line_data.get("ID", line_key),
                    "plat": line_data.get("Plat", ""),
                    "nom": line_data.get("Nom", ""),
                    "status": status,
                    "price": line_data.get("Prix"),
                }
            )

        active_items = [item for item in items if item["status"].lower() != "annulé"]
        pending_items = [item for item in active_items if item["status"].lower() != "livré"]

        orders.append(
            {
                "file": order_file,
                "id": infos.get("ID", order_file.stem.replace("commande_", "")),
                "status": infos.get("Statut", ""),
                "created_at": infos.get("Date de création", ["", ""]),
                "validation_at": infos.get("Date de validation", ["", ""]),
                "finalization_at": infos.get("Date de finalisation", ["", ""]),
                "items": items,
                "active_count": len(active_items),
                "pending_count": len(pending_items),
                "delivered_count": delivered_count,
                "cancelled_count": cancelled_count,
                "amount": infos.get("Montant"),
                "priority": bool(infos.get("Prioritaire", False)),
            }
        )

    return orders


def get_all_history_orders() -> List[Dict[str, Any]]:
    """Charge toutes les commandes de l'historique depuis les dossiers en_cours, terminee et annulee.

    Exclut les brouillons (racine du dossier commandes) et les fichiers du dossier corrompu.
    Les commandes sont triées par ID décroissant (les plus récentes en premier).
    """
    root_folder = get_command_root()
    if root_folder is None:
        return []

    folder_candidates = [
        ("en_cours", "en-cours"),
        ("terminee", "terminees", "valides", "validees"),
        ("annulee", "annulees"),
    ]

    folders_to_scan: List[Path] = []
    for candidates in folder_candidates:
        for name in candidates:
            candidate = root_folder / name
            if candidate.exists():
                folders_to_scan.append(candidate)
                break

    orders: List[Dict[str, Any]] = []
    for folder in folders_to_scan:
        for order_file in sorted(folder.glob("commande_*.json")):
            infos, command_lines = _parse_order_file(order_file)
            if not infos.get("ID"):
                continue

            items: List[Dict[str, Any]] = []
            for line_key in sorted(command_lines.keys()):
                line_data = command_lines.get(line_key, {})
                if not isinstance(line_data, dict):
                    continue
                items.append(
                    {
                        "id": line_data.get("ID", line_key),
                        "plat": line_data.get("Plat", ""),
                        "nom": line_data.get("Nom", ""),
                        "status": str(line_data.get("Statut", "")) or "Inconnu",
                        "price": line_data.get("Prix"),
                    }
                )

            orders.append(
                {
                    "file": order_file,
                    "id": infos.get("ID", order_file.stem.replace("commande_", "")),
                    "status": infos.get("Statut", ""),
                    "created_at": infos.get("Date de création", ["", ""]),
                    "validation_at": infos.get("Date de validation", ["", ""]),
                    "finalization_at": infos.get("Date de finalisation", ["", ""]),
                    "cancelled_at": infos.get("Date d'annulation", ["", ""]),
                    "items": items,
                    "amount": infos.get("Montant"),
                    "payment_type": infos.get("Type de paiement", ""),
                    "priority": bool(infos.get("Prioritaire", False)),
                }
            )

    orders.sort(key=lambda o: o.get("id", ""), reverse=True)
    return orders


def get_completed_orders() -> List[Dict[str, Any]]:
    """Charge les commandes terminées depuis le sous-dossier d'archive configuré."""
    root_folder = get_command_root()
    if root_folder is None:
        return []

    done_folder = None
    for folder_name in ("terminee", "terminees", "valides", "validees"):
        candidate = root_folder / folder_name
        if candidate.exists():
            done_folder = candidate
            break

    if done_folder is None:
        return []

    orders: List[Dict[str, Any]] = []
    for order_file in sorted(done_folder.glob("commande_*.json")):
        infos, command_lines = _parse_order_file(order_file)

        items: List[Dict[str, Any]] = []
        for line_key in sorted(command_lines.keys()):
            line_data = command_lines.get(line_key, {})
            if not isinstance(line_data, dict):
                continue
            items.append(
                {
                    "id": line_data.get("ID", line_key),
                    "plat": line_data.get("Plat", ""),
                    "nom": line_data.get("Nom", ""),
                    "status": str(line_data.get("Statut", "")) or "Inconnu",
                    "price": line_data.get("Prix"),
                }
            )

        orders.append(
            {
                "file": order_file,
                "id": infos.get("ID", order_file.stem.replace("commande_", "")),
                "status": infos.get("Statut", ""),
                "created_at": infos.get("Date de création", ["", ""]),
                "validation_at": infos.get("Date de validation", ["", ""]),
                "finalization_at": infos.get("Date de finalisation", ["", ""]),
                "items": items,
                "amount": infos.get("Montant"),
            }
        )

    return orders
