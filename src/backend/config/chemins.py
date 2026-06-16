#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chemins.py - Chemins de fichiers et dossiers dérivés du dossier data

Description:
    Calcule les chemins absolus de tous les fichiers et dossiers de données
    à partir du dossier data configuré (assets/config.json).

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

import sys
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLATS_ROOT = PROJECT_ROOT / "src" / "modules_plats"

# Noms de fichiers et dossiers fixes dans le dossier data
STOCK_FILENAME = "stock.json"
CARTE_ACTIVE_FILENAME = "carte_active.json"
CARTE_ARCHIVE_FILENAME = "carte_archive.json"
COMMANDES_DIRNAME = "commandes"
LOGS_DIRNAME = "logs"


def _default_data_folder() -> Path:
    """Retourne le dossier data par défaut selon l'environnement d'exécution."""
    if getattr(sys, "frozen", False):
        # Exécutable compilé (PyInstaller) : dossier data à côté de l'exécutable
        return Path(sys.executable).parent / "data"
    return PROJECT_ROOT / "data"


def get_data_folder() -> Path:
    """Retourne le dossier data configuré, ou le dossier par défaut si vide."""
    from src.backend.config.persistance import _load_app_config

    config = _load_app_config()
    raw = config.get("data_folder", "").strip()
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
