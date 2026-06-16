#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
utilitaires.py

Description:
    Constantes de style (couleurs, largeurs de tags) et fonctions utilitaires
    de données partagées par le module Stock (vue liste et formulaire d'édition).

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

from typing import Any, Dict, List, Optional, Set, Tuple

from src.backend.data.carte import get_card_data
from src.backend.data.prep import get_live_orders_prep

# ── Couleurs ──────────────────────────────────────────────────────────────────
_BG_MAIN        = "#2f3136"
_BG_SECTION     = "#343740"
_BG_RIGHT       = "#2f3136"
_BG_ITEM_OK     = "#3a3d43"
_BG_ITEM_OOS    = "#3d2f2f"
_BG_ITEM_SEL    = "#40454f"
_BORDER_MAIN    = "#7f7f7f"
_BORDER_SECTION = "#60646c"
_BORDER_ITEM    = "#4a4e55"
_BORDER_OOS     = "#7a3030"
_BORDER_SEL     = "#c97a30"
_TEXT_TITLE     = "#f5f5f5"
_TEXT_SECTION   = "#e0e3e8"
_TEXT_SUBGROUP  = "#b0b4bc"
_TEXT_ITEM      = "#d6d6d6"
_TEXT_ITEM_OOS  = "#a08080"
_TEXT_DIM       = "#8a8e96"

# Tags actifs
_CLR_IN_STOCK   = "#4caf50"
_CLR_OOS        = "#c0392b"
_CLR_CARTE_FG   = "#5b9bd5"
_CLR_CARTE_BG   = "#1e2d3d"
_CLR_CARTE_BD   = "#2e5a8a"
_CLR_SUIVI_FG   = "#d4a017"
_CLR_SUIVI_BG   = "#4a3a00"
_CLR_SUIVI_BD   = "#d4a017"

# Tags inactifs (grisés)
_TAG_OFF_BG = "#3b3f46"
_TAG_OFF_BD = "#4a4e55"
_TAG_OFF_FG = "#595d64"

_TAG_W_CARTE = 46
_TAG_W_SUIVI = 46
_TAG_W_ETAT  = 66


# ── Helpers de données ────────────────────────────────────────────────────────

def _build_carte_ingredients_set() -> Set[str]:
    """Collecte tous les noms d'ingrédients référencés dans la carte active."""
    try:
        card = get_card_data()
    except Exception:
        return set()
    names: Set[str] = set()

    def _traverse(node: Any) -> None:
        if not isinstance(node, dict):
            return
        for key in ("Base", "Ingrédients"):
            for name in node.get(key, []):
                if isinstance(name, str):
                    names.add(name)
        for value in node.values():
            if isinstance(value, dict):
                _traverse(value)

    _traverse(card)
    return names


def _build_prep_data() -> Tuple[Dict[Tuple[str, str], int], Dict[str, int]]:
    """
    Construit les compteurs de plats actifs (en préparation / prêts).

    Retourne :
    - by_nom  : {(catégorie_plat, nom_plat) : count}
    - by_plat : {catégorie_plat : count_total}
    """
    by_nom: Dict[Tuple[str, str], int] = {}
    by_plat: Dict[str, int] = {}
    try:
        for item in get_live_orders_prep():
            plat = item.get("plat", "")
            nom  = item.get("nom", "")
            by_nom[(plat, nom)] = by_nom.get((plat, nom), 0) + 1
            by_plat[plat]       = by_plat.get(plat, 0) + 1
    except Exception:
        pass
    return by_nom, by_plat


def _resolve_path(data: Any, path: List[str]) -> Any:
    """Navigue dans un dict imbriqué via une liste de clés."""
    node = data
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def _is_stock_leaf(node: Any) -> bool:
    """Retourne True si le nœud est une feuille de stock (article individuel)."""
    if not isinstance(node, dict):
        return False
    return (
        any(k in node for k in ("Quantité", "OutOfStock", "Valeur"))
        and not any(isinstance(v, dict) and not _is_stock_leaf(v) for v in node.values())
    )


def _get_prep_count(
    path: List[str],
    node: Dict[str, Any],
    by_nom: Dict[Tuple[str, str], int],
    by_plat: Dict[str, int],
) -> int:
    """
    Nombre de portions en préparation / prêtes pour cet article.
    Uniquement pour les plats unitaires (section "Plats" avec Quantité).

    - Avec "Valeur" (grillades) : suivi individuel par nom × Valeur.
    - Sans "Valeur" (ex. pâte à pizza) : total de la sous-catégorie.
    """
    if not path or path[0] != "Plats" or "Quantité" not in node:
        return 0
    if len(path) < 2:
        return 0
    sub_cat   = path[1]
    item_name = path[-1]
    valeur    = node.get("Valeur", 1)
    if "Valeur" in node:
        return by_nom.get((sub_cat, item_name), 0) * valeur
    return by_plat.get(sub_cat, 0)


def _collect_container_paths(data: Dict, prefix: Optional[List[str]] = None) -> List[str]:
    """Retourne tous les chemins de conteneurs (nœuds non-feuilles) du stock."""
    if prefix is None:
        prefix = []
    result: List[str] = []
    for key, value in data.items():
        if isinstance(value, dict) and not _is_stock_leaf(value):
            path = prefix + [key]
            result.append(" > ".join(path))
            result.extend(_collect_container_paths(value, path))
    return result
