#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_config.py - Configuration applicative et chemins

Description:
    Gestion de la configuration JSON (assets/config.json) : dossier data unique,
    paramètres imprimante et options d'impression.
    Les chemins de tous les fichiers de données sont dérivés du dossier data.

Author :
    Dracudar

Version:
    2.1

Date de création :
    2026.05.31

Date de modification:
    2026.06.10
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from filelock import Timeout

from src.backend import file_io


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "assets" / "config.json"
MODULES_ROOT = PROJECT_ROOT / "src" / "modules"

# Noms de fichiers et dossiers fixes dans le dossier data
STOCK_FILENAME = "stock.json"
CARTE_ACTIVE_FILENAME = "carte_active.json"
CARTE_ARCHIVE_FILENAME = "carte_archive.json"
COMMANDES_DIRNAME = "commandes"
LOGS_DIRNAME = "logs"

# Valeurs par défaut imprimante
_DEFAULT_PRINTER = {
    "vendor_id": "0x04B8",
    "product_id": "0x0E15",
    "interface": 0,
    "modele": "TM-T20II",
}


def get_assets_path(*parts: str) -> str:
    """Retourne le chemin absolu vers un fichier du dossier assets/.

    Un chemin relatif du type "assets/imgs/logo.svg" ne fonctionne que si le
    répertoire de travail courant est la racine du projet (ou de l'exécutable
    PyInstaller), ce qui n'est pas garanti — d'où la résolution via PROJECT_ROOT.
    """
    return str(PROJECT_ROOT / "assets" / Path(*parts))


def _default_data_folder() -> Path:
    """Retourne le dossier data par défaut selon l'environnement d'exécution."""
    if getattr(sys, "frozen", False):
        # Exécutable compilé (PyInstaller) : dossier data à côté de l'exécutable
        return Path(sys.executable).parent / "data"
    return PROJECT_ROOT / "data"


def _load_json_file(file_path: Path) -> Dict[str, Any]:
    """Charge un fichier JSON et retourne un dict, ou {} si absent ou invalide."""
    return file_io.charger_json(file_path)


def _load_json_file_cache(file_path: Path) -> Dict[str, Any]:
    """Charge un fichier JSON via le cache mtime ; ne re-parse que si le fichier a changé.

    Réservé aux lectures seules en boucle (affichages à rafraîchissement auto). Le
    dict renvoyé est partagé avec le cache : NE PAS le muter.
    """
    return file_io.charger_json_cache(file_path)


def _write_json_file(file_path: Path, payload: Dict[str, Any]) -> bool:
    """
    Écrit un dict dans un fichier JSON de façon atomique et sous verrou
    (crée les dossiers parents si nécessaire). Retourne True si succès.

    Le verrou protège stock.json et carte_active.json, partagés par les
    différents postes connectés sur le réseau local.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with file_io.verrou_fichier(file_path):
            return file_io.sauvegarder_json(file_path, payload)
    except Timeout:
        return False


def _load_app_config() -> Dict[str, Any]:
    """Charge le fichier de configuration applicative (assets/config.json)."""
    return _load_json_file(CONFIG_FILE)


# ── Dossier data et chemins dérivés ───────────────────────────────────────────

def data_folder_est_configure() -> bool:
    """Retourne True si un dossier data a été explicitement défini dans la config."""
    config = _load_app_config()
    return bool(config.get("data_folder", "").strip())


def get_data_folder_brut() -> str:
    """Retourne le chemin du dossier data tel que saisi (chaîne vide si non défini)."""
    config = _load_app_config()
    return config.get("data_folder", "").strip()


def get_data_folder() -> Path:
    """Retourne le dossier data configuré, ou le dossier par défaut si vide."""
    raw = get_data_folder_brut()
    return Path(raw) if raw else _default_data_folder()


def get_stock_file_path() -> Path:
    """Retourne le chemin absolu vers le fichier de stock."""
    return get_data_folder() / STOCK_FILENAME


def get_menu_file_path() -> Path:
    """Retourne le chemin absolu vers la carte active (saisie de commande)."""
    return get_data_folder() / CARTE_ACTIVE_FILENAME


def get_archive_menu_file_path() -> Path:
    """Retourne le chemin absolu vers la carte archive (module carte)."""
    return get_data_folder() / CARTE_ARCHIVE_FILENAME


def get_archive_folder_path() -> Path:
    """Retourne le chemin absolu vers le dossier des commandes archivées."""
    return get_data_folder() / COMMANDES_DIRNAME


def get_logs_folder_path() -> Path:
    """Retourne le chemin absolu vers le dossier des logs."""
    return get_data_folder() / LOGS_DIRNAME


def get_command_root() -> Optional[Path]:
    """Retourne le dossier des commandes s'il existe, None sinon."""
    folder = get_archive_folder_path()
    return folder if folder.exists() else None


# ── Imprimante ─────────────────────────────────────────────────────────────────

def _parse_hex_or_int(value: Any, default: int) -> int:
    """Convertit une valeur hex string ('0x04B8') ou entier en int."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 16) if value.startswith("0x") or value.startswith("0X") else int(value)
        except ValueError:
            pass
    return default


def get_printer_config() -> Dict[str, Any]:
    """Retourne la configuration de l'imprimante thermique avec les valeurs par défaut si absente."""
    config = _load_app_config()
    printer = config.get("imprimante", {})
    return {
        "vendor_id": _parse_hex_or_int(printer.get("vendor_id", _DEFAULT_PRINTER["vendor_id"]), 0x04B8),
        "product_id": _parse_hex_or_int(printer.get("product_id", _DEFAULT_PRINTER["product_id"]), 0x0E15),
        "interface": int(printer.get("interface", _DEFAULT_PRINTER["interface"])),
        "modele": str(printer.get("modele", _DEFAULT_PRINTER["modele"])),
    }


# ── Options d'impression ───────────────────────────────────────────────────────

def get_print_options() -> Dict[str, bool]:
    """Retourne les options d'activation de l'impression (globale, ticket client et cuisine)."""
    config = _load_app_config()
    impression = config.get("impression", {})
    return {
        "impression_active": bool(impression.get("impression_active", True)),
        "ticket_client": bool(impression.get("ticket_client", True)),
        "ticket_cuisine": bool(impression.get("ticket_cuisine", True)),
    }


# ── Sauvegarde ─────────────────────────────────────────────────────────────────

def _create_data_structure(data_folder: Path) -> bool:
    """Crée la structure de dossiers et les fichiers JSON vides si absents. Vérifie les fichiers existants."""
    from src.backend import logger
    try:
        data_folder.mkdir(parents=True, exist_ok=True)

        # Dossiers principaux
        for sous_dossier, type_dossier in [
            (COMMANDES_DIRNAME, "commandes"),
            (LOGS_DIRNAME, "logs"),
        ]:
            chemin = data_folder / sous_dossier
            creation = not chemin.exists()
            chemin.mkdir(exist_ok=True)
            if creation:
                logger.log(logger.CREATION_DOSSIER, {"chemin": str(chemin), "type": type_dossier})

        # Sous-dossiers de commandes/
        commandes_path = data_folder / COMMANDES_DIRNAME
        for sous_dossier in ("en_cours", "terminee", "annulee", "corrompu"):
            chemin = commandes_path / sous_dossier
            creation = not chemin.exists()
            chemin.mkdir(exist_ok=True)
            if creation:
                logger.log(logger.CREATION_DOSSIER, {
                    "chemin": str(chemin),
                    "type": f"commandes/{sous_dossier}",
                })

        # Fichiers JSON : création si absents, vérification si existants
        for filename in (STOCK_FILENAME, CARTE_ACTIVE_FILENAME, CARTE_ARCHIVE_FILENAME):
            file_path = data_folder / filename
            if not file_path.exists():
                _write_json_file(file_path, {})
                logger.log(logger.CREATION_FICHIER, {
                    "chemin": str(file_path),
                    "fichier": filename,
                })
            else:
                try:
                    with file_path.open("r", encoding="utf-8") as fh:
                        json.load(fh)
                except (OSError, json.JSONDecodeError):
                    logger.log(logger.FICHIER_CORROMPU, {
                        "chemin": str(file_path),
                        "fichier": filename,
                    })

    except OSError:
        return False
    return True


def initialiser_dossier_data() -> bool:
    """Crée la structure du dossier data si un chemin est configuré. Ne fait rien sinon."""
    if not data_folder_est_configure():
        return True
    return _create_data_structure(get_data_folder())


def save_app_config(
    data_folder: str,
    vendor_id: str,
    product_id: str,
    interface: int,
    modele: str,
    impression_active: bool,
    ticket_client: bool,
    ticket_cuisine: bool,
) -> bool:
    """Persiste toute la configuration et crée la structure data si nécessaire. Retourne True si succès."""
    if data_folder.strip():
        folder_path = Path(data_folder.strip())
        if not _create_data_structure(folder_path):
            return False

    payload = {
        "data_folder": data_folder.strip(),
        "imprimante": {
            "vendor_id": vendor_id.strip(),
            "product_id": product_id.strip(),
            "interface": interface,
            "modele": modele.strip(),
        },
        "impression": {
            "impression_active": impression_active,
            "ticket_client": ticket_client,
            "ticket_cuisine": ticket_cuisine,
        },
    }
    return _write_json_file(CONFIG_FILE, payload)


def get_default_config() -> Dict[str, Any]:
    """Retourne la configuration par défaut complète (indépendante de toute valeur persistée)."""
    return {
        "data_folder": "",
        "imprimante": dict(_DEFAULT_PRINTER),
        "impression": {"impression_active": True, "ticket_client": True, "ticket_cuisine": True},
    }
