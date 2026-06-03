#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_sources.py - Sources de données métier

Description:
    Chargement et sauvegarde des données de la carte, du stock et des commandes.
    Fournit également les catégories enrichies (icône, état, recettes) utilisées
    par les vues de saisie de commande.

Author :
    Dracudar

Version:
    2.0

Date de création :
    2026.05.18

Date de modification:
    2026.05.31
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.backend.app_config import (
    MODULES_ROOT,
    _load_json_file,
    _write_json_file,
    get_archive_folder_path,
    get_command_root,
    get_menu_file_path,
    get_stock_file_path,
)


# ── Carte / menu ──────────────────────────────────────────────────────────────

def get_card_data() -> Dict[str, Any]:
    """Charge la carte snack depuis le fichier JSON configuré."""
    return _load_json_file(get_menu_file_path())


def save_card_data(payload: Dict[str, Any]) -> bool:
    """Sauvegarde la carte snack dans le fichier JSON configuré. Retourne True si succès."""
    return _write_json_file(get_menu_file_path(), payload)


# ── Stock ─────────────────────────────────────────────────────────────────────

def get_stock_data() -> Dict[str, Any]:
    """Charge le stock depuis le fichier JSON configuré."""
    return _load_json_file(get_stock_file_path())


def save_stock_data(payload: Dict[str, Any]) -> bool:
    """Sauvegarde le stock dans le fichier JSON configuré. Retourne True si succès."""
    return _write_json_file(get_stock_file_path(), payload)


# ── Catégories et icônes ──────────────────────────────────────────────────────

def _normalize_text(value: str) -> str:
    """Convertit une chaîne en identifiant normalisé ASCII bas de casse sans ponctuation."""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_text.lower())


def _normalized_state(state: str) -> str:
    """Normalise un état de catégorie pour comparaison insensible à la casse et aux accents."""
    return _normalize_text(state.strip())


def _find_category_folder(category_name: str) -> Optional[Path]:
    """Recherche le dossier de module correspondant à une catégorie par nom normalisé."""
    if not MODULES_ROOT.exists():
        return None
    target = _normalize_text(category_name)
    for child in MODULES_ROOT.iterdir():
        if child.is_dir() and _normalize_text(child.name) == target:
            return child
    return None


def _resolve_category_icon(category_name: str, out_of_stock: bool) -> Optional[str]:
    """Retourne le chemin de l'icône SVG/PNG la plus appropriée pour une catégorie.

    Préfère icon_HS.* si la catégorie est en rupture de stock, sinon icon.svg.
    """
    folder = _find_category_folder(category_name)
    if folder is None:
        return None
    preferred_files = ["icon.svg"]
    if out_of_stock:
        preferred_files = ["icon_HS.svg", "icon_HS.png", "icon.svg", "icon.png"]
    for icon_name in preferred_files:
        icon_path = folder / icon_name
        if icon_path.exists():
            return str(icon_path)
    return None


def get_menu_categories() -> List[Dict[str, Any]]:
    """Retourne les catégories de la carte sous forme normalisée, avec état, icône et comptage de recettes."""
    card_data = get_card_data()
    categories: List[Dict[str, Any]] = []

    for category_name, payload in card_data.items():
        if not isinstance(payload, dict):
            payload = {}

        recipes = payload.get("Recettes")
        recipe_count = len(recipes) if isinstance(recipes, dict) else 0
        state = str(payload.get("Etat", "")).strip()
        normalized_state = _normalized_state(state)
        is_hidden = normalized_state in {"retire", "archive"}
        is_out_of_stock = normalized_state in {"outofstock", "rupture", "horsstock"}
        is_available = normalized_state in {"disponible", ""}

        categories.append(
            {
                "name": category_name,
                "state": state,
                "price": payload.get("Prix"),
                "recipe_count": recipe_count,
                "has_recipes": isinstance(recipes, dict) and recipe_count > 0,
                "hidden": is_hidden,
                "out_of_stock": is_out_of_stock,
                "enabled": is_available and not is_out_of_stock and not is_hidden,
                "icon_path": _resolve_category_icon(category_name, is_out_of_stock),
            }
        )

    return categories


# ── Commandes ─────────────────────────────────────────────────────────────────

def get_draft_orders() -> List[Dict[str, Any]]:
    """Load draft orders (being typed) from root commandes folder. Max 1 active draft at a time."""
    root_folder = get_command_root()
    if root_folder is None:
        return []

    if not root_folder.exists():
        return []

    orders: List[Dict[str, Any]] = []
    for order_file in sorted(root_folder.glob("commande_*.json")):
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
            }
        )

    return orders


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
                "delivery_at": infos.get("Date de livraison", ["", ""]),
                "items": items,
                "active_count": len(active_items),
                "pending_count": len(pending_items),
                "delivered_count": delivered_count,
                "cancelled_count": cancelled_count,
                "amount": infos.get("Montant"),
            }
        )

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
                "delivery_at": infos.get("Date de livraison", ["", ""]),
                "items": items,
                "amount": infos.get("Montant"),
            }
        )

    return orders
