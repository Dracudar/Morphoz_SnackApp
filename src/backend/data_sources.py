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
    2.4

Date de création :
    2026.05.18

Date de modification:
    2026.06.10
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.backend.app_config import (
    MODULES_ROOT,
    _load_json_file,
    _write_json_file,
    get_archive_folder_path,
    get_archive_menu_file_path,
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


def get_archive_card_data() -> Dict[str, Any]:
    """Charge la carte archive depuis le fichier JSON configuré."""
    return _load_json_file(get_archive_menu_file_path())


def save_archive_card_data(payload: Dict[str, Any]) -> bool:
    """Sauvegarde la carte archive dans le fichier JSON configuré. Retourne True si succès."""
    return _write_json_file(get_archive_menu_file_path(), payload)


# ── Stock ─────────────────────────────────────────────────────────────────────

def get_stock_data() -> Dict[str, Any]:
    """Charge le stock depuis le fichier JSON configuré."""
    return _load_json_file(get_stock_file_path())


def save_stock_data(payload: Dict[str, Any]) -> bool:
    """Sauvegarde le stock dans le fichier JSON configuré. Retourne True si succès."""
    return _write_json_file(get_stock_file_path(), payload)


_stock_cache_instance = None


def _reconcilier_brouillons(cache) -> None:
    """
    Décrémente le cache pour les plats "En attente" présents dans les brouillons
    (commandes "En saisie" non encore validées).

    Nécessaire au démarrage après un crash ou une coupure : le stock n'est sauvegardé
    sur disque qu'à la validation, donc un brouillon laissé par un arrêt imprévu contient
    des ingrédients qui ne sont pas reflétés dans le fichier stock.

    Seuls les fichiers à la racine du dossier commandes sont examinés (pas les
    sous-dossiers en_cours, terminee, annulee).
    """
    root_folder = get_command_root()
    if root_folder is None or not root_folder.exists():
        return

    for order_file in sorted(root_folder.glob("commande_*.json")):
        try:
            with open(str(order_file), "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        if data.get("Informations", {}).get("Statut") != "En saisie":
            continue

        for plat in data.get("Commande", {}).values():
            if plat.get("Statut") != "En attente":
                continue
            plat_type = plat.get("Plat", "")
            composition = plat.get("Composition", {})
            if plat_type == "Pizza":
                cache.decrementer(["Plats", "Pizza", "Pâte à pizza"])
            elif plat_type == "Grillade":
                for viande, qte in composition.get("Viandes", {}).items():
                    cache.decrementer(["Plats", "Grillades", viande], qte)


def get_stock_cache():
    """Retourne l'instance singleton du cache de stock pour la session en cours.

    Le cache est initialisé à partir du fichier JSON au premier appel, puis
    partagé entre tous les modules. Les modifications ne sont persistées sur
    disque que via cache.save() (appelé à la validation d'une commande ou à
    l'annulation d'un plat post-validation).

    À l'initialisation, les brouillons existants (commandes "En saisie") sont
    réconciliés : leurs plats "En attente" sont décrémentés du cache pour
    refléter les ingrédients déjà réservés mais non encore persistés sur disque.
    """
    global _stock_cache_instance
    if _stock_cache_instance is None:
        from src.modules.stock.cache import StockCache
        _stock_cache_instance = StockCache(str(get_stock_file_path()))
        _reconcilier_brouillons(_stock_cache_instance)
    return _stock_cache_instance


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


# ── Commandes ─────────────────────────────────────────────────────────────────

def get_draft_orders() -> List[Dict[str, Any]]:
    """Charge les commandes en brouillon (en cours de saisie) depuis le dossier racine des commandes. Maximum 1 brouillon actif à la fois."""
    root_folder = get_command_root()
    if root_folder is None:
        return []

    if not root_folder.exists():
        return []

    orders: List[Dict[str, Any]] = []
    # Only search in root folder, not in subdirectories
    files = [root_folder / f for f in os.listdir(str(root_folder)) if f.startswith("commande_") and f.endswith(".json")]

    for order_file in sorted(files):
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
                "priority": bool(infos.get("Prioritaire", False)),
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
                "priority": bool(infos.get("Prioritaire", False)),
            }
        )

    return orders


def get_live_orders_prep() -> List[Dict[str, Any]]:
    """Charge les plats actifs des commandes en cours, pour le poste de préparation.

    Retourne une liste plate (un dict par plat) avec composition complète, triée par ID de
    commande puis par ID de plat. Exclut les plats au statut Annulé et Livré.
    """
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

    plats: List[Dict[str, Any]] = []
    for order_file in sorted(live_folder.glob("commande_*.json")):
        payload = _load_json_file(order_file)
        infos = payload.get("Informations", {})
        if not isinstance(infos, dict):
            infos = {}
        order_id = infos.get("ID", order_file.stem.replace("commande_", ""))
        command_lines = payload.get("Commande", {})
        if not isinstance(command_lines, dict):
            continue

        for line_key in sorted(command_lines.keys()):
            line_data = command_lines.get(line_key, {})
            if not isinstance(line_data, dict):
                continue

            status = str(line_data.get("Statut", "")).strip() or "Inconnu"
            if status.lower() in ("annulé", "livré", "non livré"):
                continue

            plats.append({
                "order_id": order_id,
                "file": order_file,
                "id": line_data.get("ID", line_key),
                "plat": line_data.get("Plat", ""),
                "nom": line_data.get("Nom", ""),
                "status": status,
                "composition": line_data.get("Composition", {}),
                "prix": line_data.get("Prix"),
            })

    return plats


def get_all_history_orders() -> List[Dict[str, Any]]:
    """Charge toutes les commandes de l'historique depuis les dossiers en_cours, terminee et annulee.

    Exclut les brouillons (racine du dossier commandes) et les fichiers du dossier corrompu.
    Les commandes sont triées par ID décroissant (les plus récentes en premier).
    """
    root_folder = get_command_root()
    if root_folder is None:
        return []

    folder_candidates = [
        ("en_cours", "en-cours"),
        ("terminee", "terminees", "valides", "validees"),
        ("annulee", "annulees"),
    ]

    folders_to_scan: List[Path] = []
    for candidates in folder_candidates:
        for name in candidates:
            candidate = root_folder / name
            if candidate.exists():
                folders_to_scan.append(candidate)
                break

    orders: List[Dict[str, Any]] = []
    for folder in folders_to_scan:
        for order_file in sorted(folder.glob("commande_*.json")):
            infos, command_lines = _parse_order_file(order_file)
            if not infos.get("ID"):
                continue

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
                    "cancelled_at": infos.get("Date d'annulation", ["", ""]),
                    "items": items,
                    "amount": infos.get("Montant"),
                    "payment_type": infos.get("Type de paiement", ""),
                    "priority": bool(infos.get("Prioritaire", False)),
                }
            )

    orders.sort(key=lambda o: o.get("id", ""), reverse=True)
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
