#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plats_router.py

Description:
    Orchestrateur de routage vers les handlers de plats par catégorie.

    Ordre de résolution du module pour un plat donné :
    1. Champ "module" dans la carte (ex. "module": "cafe")
    2. Découverte automatique par slug normalisé (ex. "Mr Freez" → mr_freez)
    3. Fallback : ajout direct sans dialogue (plats simples sans personnalisation)

    Chaque module résolu doit exposer une fonction route_selection(context, command_path).

Author :
    Dracudar

Version:
    2.1

Date de création :
    2026.05.31

Date de modification:
    2026.06.15
"""

import importlib
import importlib.util
import re
import unicodedata
from typing import Optional, Dict

from src.backend import logger
from src.backend.data_sources import get_card_data


def route_plat_selection(plat_name: str, context, command_path: str) -> Optional[Dict]:
    """Dispatche la sélection d'un plat vers le handler approprié.

    Args:
        plat_name: Nom du plat tel qu'il apparaît dans la carte (ex. "Pizza", "Mr Freez").
        context: Objet contexte (peut être None).
        command_path: Chemin vers le fichier de commande courant.

    Returns:
        Dict du plat à ajouter à la commande, ou None si annulation/erreur.
    """
    card_data = get_card_data()

    if plat_name not in card_data:
        logger.log(logger.ERREUR, {
            "contexte": "routage_plat",
            "message": f"Type de plat inconnu : {plat_name}",
        })
        return None

    plat_data = card_data[plat_name]
    module_path = _resolve_module_path(plat_name, plat_data)

    if module_path:
        try:
            module = importlib.import_module(module_path)
            return module.route_selection(context, command_path)
        except Exception as e:
            logger.log(logger.ERREUR, {
                "contexte": "routage_plat",
                "type_erreur": type(e).__name__,
                "message": str(e),
                "type_plat": plat_name,
            })
            return None

    return _route_ajout_direct(plat_name, plat_data)


# ── Résolution du module ───────────────────────────────────────────────────────

def _resolve_module_path(plat_name: str, plat_data: Dict) -> Optional[str]:
    """Résout le chemin du module rooting pour un plat.

    Priorité : champ "module" explicite > découverte par slug > None.
    """
    # 1. Champ explicite dans la carte
    if "module" in plat_data:
        return f"src.modules.plats.{plat_data['module']}.rooting"

    # 2. Découverte automatique par slug normalisé
    slug = _to_slug(plat_name)
    candidate = f"src.modules.plats.{slug}.rooting"
    try:
        if importlib.util.find_spec(candidate) is not None:
            return candidate
    except ModuleNotFoundError:
        pass

    return None


def _to_slug(name: str) -> str:
    """Convertit un nom de plat en slug Python (sans accents, minuscules, underscores)."""
    sans_accents = unicodedata.normalize("NFD", name)
    sans_accents = "".join(c for c in sans_accents if unicodedata.category(c) != "Mn")
    return re.sub(r"[\s\-]+", "_", sans_accents).lower()


# ── Fallback ajout direct ──────────────────────────────────────────────────────

def _route_ajout_direct(plat_name: str, plat_data: Dict) -> Optional[Dict]:
    """Ajoute directement un plat simple à la commande sans dialogue.

    Utilisé pour les plats sans personnalisation et sans module dédié.
    Retourne None si le plat n'a pas de prix défini dans la carte.
    """
    prix = plat_data.get("Prix")
    if prix is None:
        logger.log(logger.ERREUR, {
            "contexte": "routage_plat",
            "message": f"Prix manquant pour ajout direct : {plat_name}",
        })
        return None

    return {
        "Plat": plat_name,
        "Nom": plat_name,
        "Prix": prix,
        "Statut": "En attente",
        "Composition": [],
    }
