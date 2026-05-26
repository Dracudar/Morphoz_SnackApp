#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_sources.py - Sources de donnees UI

Description:
    Fonctions utilitaires pour charger la carte et les commandes en cours.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.18

Date de modification:
    2026.05.18
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_FILE = PROJECT_ROOT / "assets" / "config.json"
DEFAULT_CARD_FILE = PROJECT_ROOT / "data" / "carte_snack.json"
DEFAULT_STOCK_FILE = PROJECT_ROOT / "data" / "stock.json"
MODULES_ROOT = PROJECT_ROOT / "src" / "modules"
COMMAND_ROOT_CANDIDATES = [
    PROJECT_ROOT / "data" / "commandes",
    PROJECT_ROOT / "tests" / "data" / "commandes",
]


def _load_json_file(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        return {}

    try:
        with file_path.open("r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        return {}

    if isinstance(data, dict):
        return data
    return {}


def _write_json_file(file_path: Path, payload: Dict[str, Any]) -> bool:
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, ensure_ascii=False, indent=4)
    except OSError:
        return False
    return True


def _load_app_config() -> Dict[str, Any]:
    config = _load_json_file(CONFIG_FILE)
    if not config:
        return {}
    return config


def get_app_paths() -> Dict[str, str]:
    config = _load_app_config()
    return {
        "stock_file": str(Path(config.get("stock_file", DEFAULT_STOCK_FILE))),
        "menu_file": str(Path(config.get("menu_file", DEFAULT_CARD_FILE))),
        "archive_folder": str(Path(config.get("archive_folder", PROJECT_ROOT / "data"))),
    }


def get_default_app_paths() -> Dict[str, str]:
    return {
        "stock_file": str(DEFAULT_STOCK_FILE),
        "menu_file": str(DEFAULT_CARD_FILE),
        "archive_folder": str(PROJECT_ROOT / "data"),
    }


def save_app_paths(stock_file: str, menu_file: str, archive_folder: str) -> bool:
    return _write_json_file(
        CONFIG_FILE,
        {
            "stock_file": stock_file,
            "menu_file": menu_file,
            "archive_folder": archive_folder,
        },
    )


def get_stock_file_path() -> Path:
    return Path(get_app_paths()["stock_file"])


def get_menu_file_path() -> Path:
    return Path(get_app_paths()["menu_file"])


def get_archive_folder_path() -> Path:
    return Path(get_app_paths()["archive_folder"])


def get_card_data() -> Dict[str, Any]:
    """Charge la carte snack depuis le fichier JSON principal."""
    return _load_json_file(get_menu_file_path())


def save_card_data(payload: Dict[str, Any]) -> bool:
    return _write_json_file(get_menu_file_path(), payload)


def get_stock_data() -> Dict[str, Any]:
    return _load_json_file(get_stock_file_path())


def save_stock_data(payload: Dict[str, Any]) -> bool:
    return _write_json_file(get_stock_file_path(), payload)


def _normalize_text(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_text.lower())


def _normalized_state(state: str) -> str:
    return _normalize_text(state.strip())


def _find_category_folder(category_name: str) -> Optional[Path]:
    if not MODULES_ROOT.exists():
        return None

    target = _normalize_text(category_name)
    for child in MODULES_ROOT.iterdir():
        if not child.is_dir():
            continue
        if _normalize_text(child.name) == target:
            return child

    return None


def _resolve_category_icon(category_name: str, out_of_stock: bool) -> Optional[str]:
    folder = _find_category_folder(category_name)
    if folder is None:
        return None

    preferred_files = ["icon.svg", "icon.png", "icon_HS.svg", "icon_HS.png"]
    if out_of_stock:
        preferred_files = ["icon_HS.svg", "icon_HS.png", "icon.svg", "icon.png"]

    for icon_name in preferred_files:
        icon_path = folder / icon_name
        if icon_path.exists():
            return str(icon_path)

    return None


def get_menu_categories() -> List[Dict[str, Any]]:
    """Retourne les categories de la carte sous forme normalisee."""
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


def get_command_root() -> Optional[Path]:
    """Retourne le dossier racine des commandes si disponible."""
    archive_root = get_archive_folder_path()
    candidates = [archive_root / "commandes", archive_root]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    for candidate in COMMAND_ROOT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def get_live_orders() -> List[Dict[str, Any]]:
    """Charge les commandes depuis le sous-dossier `en_cours`."""
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
        payload = _load_json_file(order_file)
        infos = payload.get("Informations", {}) if isinstance(payload.get("Informations", {}), dict) else {}
        command_lines = payload.get("Commande", {})
        if not isinstance(command_lines, dict):
            command_lines = {}

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
    """Charge les commandes terminees depuis le dossier d'archive configure."""
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
        payload = _load_json_file(order_file)
        infos = payload.get("Informations", {}) if isinstance(payload.get("Informations", {}), dict) else {}
        command_lines = payload.get("Commande", {})
        if not isinstance(command_lines, dict):
            command_lines = {}

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