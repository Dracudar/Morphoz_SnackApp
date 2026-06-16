#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
carte.py - Données de la carte snack (active et archive)

Description:
    Chargement et sauvegarde de la carte active (saisie de commande) et de
    la carte archive (module carte).

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

from typing import Any, Dict

from src.backend.config.chemins import get_archive_menu_file_path, get_menu_file_path
from src.backend.config.persistance import _load_json_file, _write_json_file


def get_card_data() -> Dict[str, Any]:
    """Charge la carte snack depuis le fichier JSON configuré."""
    return _load_json_file(get_menu_file_path())


def save_card_data(payload: Dict[str, Any]) -> bool:
    """Sauvegarde la carte snack dans le fichier JSON configuré. Retourne True si succès."""
    return _write_json_file(get_menu_file_path(), payload)


def get_archive_card_data() -> Dict[str, Any]:
    """Charge la carte archive depuis le fichier JSON configuré."""
    return _load_json_file(get_archive_menu_file_path())


def save_archive_card_data(payload: Dict[str, Any]) -> bool:
    """Sauvegarde la carte archive dans le fichier JSON configuré. Retourne True si succès."""
    return _write_json_file(get_archive_menu_file_path(), payload)
