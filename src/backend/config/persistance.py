#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
persistance.py - Lecture/écriture JSON et sauvegarde de la configuration applicative

Description:
    Helpers JSON génériques, chargement de assets/config.json, création de la
    structure du dossier data et sauvegarde de la configuration complète.

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

import json
from pathlib import Path
from typing import Any, Dict

from src.backend.config.chemins import (
    CARTE_ACTIVE_FILENAME,
    CARTE_ARCHIVE_FILENAME,
    COMMANDES_DIRNAME,
    LOGS_DIRNAME,
    PROJECT_ROOT,
    STOCK_FILENAME,
    _default_data_folder,
)


CONFIG_FILE = PROJECT_ROOT / "assets" / "config.json"


def _load_json_file(file_path: Path) -> Dict[str, Any]:
    """Charge un fichier JSON et retourne un dict, ou {} si absent ou invalide."""
    if not file_path.exists():
        return {}
    try:
        with file_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_json_file(file_path: Path, payload: Dict[str, Any]) -> bool:
    """Écrit un dict dans un fichier JSON (crée les dossiers parents si nécessaire). Retourne True si succès."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=4)
    except OSError:
        return False
    return True


def _load_app_config() -> Dict[str, Any]:
    """Charge le fichier de configuration applicative (assets/config.json)."""
    return _load_json_file(CONFIG_FILE)


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
    folder_path = Path(data_folder.strip()) if data_folder.strip() else _default_data_folder()

    if not _create_data_structure(folder_path):
        return False

    payload = {
        "data_folder": str(folder_path),
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
    from src.backend.config.imprimante import _DEFAULT_PRINTER

    return {
        "data_folder": str(_default_data_folder()),
        "imprimante": dict(_DEFAULT_PRINTER),
        "impression": {"impression_active": True, "ticket_client": True, "ticket_cuisine": True},
    }
