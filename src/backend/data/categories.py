#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
categories.py - Catégories enrichies de la carte (icône, état, recettes)

Description:
    Construit la liste des catégories de la carte active utilisée par les
    vues de saisie de commande : état normalisé, icône résolue depuis
    src/modules_plats/, comptage de recettes.

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

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.backend.config.chemins import PLATS_ROOT
from src.backend.data.carte import get_card_data


def _normalize_text(value: str) -> str:
    """Convertit une chaîne en identifiant normalisé ASCII bas de casse sans ponctuation."""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_text.lower())


def _normalized_state(state: str) -> str:
    """Normalise un état de catégorie pour comparaison insensible à la casse et aux accents."""
    return _normalize_text(state.strip())


def _find_category_folder(category_name: str) -> Optional[Path]:
    """Recherche le dossier de plat correspondant à une catégorie par nom normalisé."""
    if not PLATS_ROOT.exists():
        return None
    target = _normalize_text(category_name)
    for child in PLATS_ROOT.iterdir():
        if child.is_dir() and _normalize_text(child.name) == target:
            return child
    return None


def _resolve_category_icon(category_name: str, out_of_stock: bool) -> Optional[str]:
    """Retourne le chemin de l'icône SVG la plus appropriée pour une catégorie.

    Préfère icon_HS.* si la catégorie est en rupture de stock, sinon icon.svg.
    """
    folder = _find_category_folder(category_name)
    if folder is None:
        return None
    preferred_files = ["icon.svg"]
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
