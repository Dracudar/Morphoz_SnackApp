#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_config.py - Configuration applicative et chemins

Description:
    Gestion de la configuration JSON et résolution des chemins des fichiers
    de données (menu, stock, archives). Point d'entrée unique pour accéder
    aux chemins configurés ou aux valeurs par défaut.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.31

Date de modification:
    2026.05.31
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "assets" / "config.json"
DEFAULT_CARD_FILE = PROJECT_ROOT / "data" / "carte_snack.json"
DEFAULT_STOCK_FILE = PROJECT_ROOT / "data" / "stock.json"
MODULES_ROOT = PROJECT_ROOT / "src" / "modules"
COMMAND_ROOT_CANDIDATES = [
    PROJECT_ROOT / "data" / "commandes",
    PROJECT_ROOT / "tests" / "data" / "commandes",
]


def _load_json_file(file_path: Path) -> Dict[str, Any]:
    """Charge un fichier JSON et retourne un dict, ou {} si absent ou invalide."""
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
    """Écrit un dict dans un fichier JSON (crée les dossiers parents si nécessaire). Retourne True si succès."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, ensure_ascii=False, indent=4)
    except OSError:
        return False
    return True


def _load_app_config() -> Dict[str, Any]:
    """Charge le fichier de configuration applicative (assets/config.json)."""
    return _load_json_file(CONFIG_FILE)


def get_app_paths() -> Dict[str, str]:
    """Retourne les chemins configurés (stock, menu, archive), avec les valeurs par défaut si la config est absente."""
    config = _load_app_config()
    return {
        "stock_file": str(Path(config.get("stock_file", DEFAULT_STOCK_FILE))),
        "menu_file": str(Path(config.get("menu_file", DEFAULT_CARD_FILE))),
        "archive_folder": str(Path(config.get("archive_folder", PROJECT_ROOT / "data"))),
    }


def get_default_app_paths() -> Dict[str, str]:
    """Retourne les chemins par défaut (indépendant de toute configuration persistée)."""
    return {
        "stock_file": str(DEFAULT_STOCK_FILE),
        "menu_file": str(DEFAULT_CARD_FILE),
        "archive_folder": str(PROJECT_ROOT / "data"),
    }


def save_app_paths(stock_file: str, menu_file: str, archive_folder: str) -> bool:
    """Persiste les chemins personnalisés dans le fichier de configuration. Retourne True si succès."""
    return _write_json_file(
        CONFIG_FILE,
        {
            "stock_file": stock_file,
            "menu_file": menu_file,
            "archive_folder": archive_folder,
        },
    )


def get_stock_file_path() -> Path:
    """Retourne le chemin absolu vers le fichier de stock configuré."""
    return Path(get_app_paths()["stock_file"])


def get_menu_file_path() -> Path:
    """Retourne le chemin absolu vers le fichier de carte/menu configuré."""
    return Path(get_app_paths()["menu_file"])


def get_archive_folder_path() -> Path:
    """Retourne le chemin absolu vers le dossier d'archive configuré."""
    return Path(get_app_paths()["archive_folder"])


def get_command_root() -> Optional[Path]:
    """Retourne le dossier racine des commandes si disponible, None sinon.

    Cherche d'abord dans le dossier d'archive configuré, puis dans les
    emplacements par défaut (data/commandes, tests/data/commandes).
    """
    archive_root = get_archive_folder_path()
    candidates = [archive_root / "commandes", archive_root]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    for candidate in COMMAND_ROOT_CANDIDATES:
        if candidate.exists():
            return candidate
    return None
