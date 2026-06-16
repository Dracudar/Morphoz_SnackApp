#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stock.py - Données de stock et cache en mémoire

Description:
    Chargement/sauvegarde du stock JSON, classe StockCache (cache en mémoire
    avec suivi des modifications) et singleton partagé par les modules.

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

import copy
import json
from typing import Any, Dict

from src.backend.config.chemins import get_command_root, get_stock_file_path
from src.backend.config.persistance import _load_json_file, _write_json_file


# ── Accès fichier ─────────────────────────────────────────────────────────────

def get_stock_data() -> Dict[str, Any]:
    """Charge le stock depuis le fichier JSON configuré."""
    return _load_json_file(get_stock_file_path())


def save_stock_data(payload: Dict[str, Any]) -> bool:
    """Sauvegarde le stock dans le fichier JSON configuré. Retourne True si succès."""
    return _write_json_file(get_stock_file_path(), payload)


# ── Cache en mémoire ──────────────────────────────────────────────────────────

class StockCache:
    """Cache en mémoire du stock avec suivi des modifications par rapport aux valeurs d'origine."""

    def __init__(self, chemin_stock_json):
        """
        Charge le stock depuis le fichier JSON et initialise le cache.

        :param chemin_stock_json: Chemin absolu vers le fichier JSON de stock.
        """
        self.chemin_stock_json = chemin_stock_json
        self._stock_original = self._charger_stock()
        self._stock_cache = copy.deepcopy(self._stock_original)

    def _charger_stock(self):
        """Lit et retourne le contenu du fichier JSON de stock."""
        with open(self.chemin_stock_json, encoding="utf-8") as f:
            return json.load(f)

    def reset_cache(self):
        """Réinitialise le cache à partir des valeurs originales chargées."""
        self._stock_cache = copy.deepcopy(self._stock_original)

    def save(self):
        """Persiste le cache modifié sur disque et met à jour les valeurs d'origine."""
        with open(self.chemin_stock_json, "w", encoding="utf-8") as f:
            json.dump(self._stock_cache, f, indent=2, ensure_ascii=False)
        self._stock_original = copy.deepcopy(self._stock_cache)

    def get_quantite(self, chemin):
        """
        Retourne la quantité d'un article identifié par son chemin de clés.

        :param chemin: Liste de clés JSON (ex. ['Plats', 'Pizza', 'Pâte à pizza']).
        """
        ref = self._stock_cache
        for key in chemin:
            ref = ref[key]
        return ref.get("Quantité", None)

    def decrementer(self, chemin, n=1):
        """
        Décrémente la quantité d'un article de n unités. Passe OutOfStock à True si la quantité atteint 0.

        :param chemin: Liste de clés JSON vers l'article.
        :param n: Nombre d'unités à décrémenter (défaut : 1).
        :return: True si l'opération a réussi, False sinon.
        """
        ref = self._stock_cache
        for key in chemin[:-1]:
            ref = ref[key]
        elem = ref[chemin[-1]]
        if "Quantité" in elem and elem["Quantité"] >= n:
            elem["Quantité"] -= n
            if elem["Quantité"] == 0:
                elem["OutOfStock"] = True
            return True
        return False

    def incrementer(self, chemin, n=1):
        """
        Incrémente la quantité d'un article de n unités. Repasse OutOfStock à False si la quantité devient positive.

        :param chemin: Liste de clés JSON vers l'article.
        :param n: Nombre d'unités à incrémenter (défaut : 1).
        :return: True si l'opération a réussi, False sinon.
        """
        ref = self._stock_cache
        for key in chemin[:-1]:
            ref = ref[key]
        elem = ref[chemin[-1]]
        if "Quantité" in elem:
            elem["Quantité"] += n
            if elem["Quantité"] > 0:
                elem["OutOfStock"] = False
            return True
        return False

    def is_out_of_stock(self, chemin):
        """
        Retourne True si l'article est marqué comme hors stock dans le cache.

        :param chemin: Liste de clés JSON vers l'article.
        """
        ref = self._stock_cache
        for key in chemin:
            ref = ref[key]
        return ref.get("OutOfStock", False)

    def set_out_of_stock(self, chemin, valeur):
        """
        Définit directement l'état OutOfStock d'un article dans le cache en mémoire.

        :param chemin: Liste de clés JSON vers l'article.
        :param valeur: True = rupture, False = en stock.
        :return: True si l'opération a réussi, False sinon.
        """
        try:
            ref = self._stock_cache
            for key in chemin:
                ref = ref[key]
            ref["OutOfStock"] = valeur
            return True
        except (KeyError, TypeError):
            return False

    def set_quantite(self, chemin, valeur):
        """
        Définit directement la quantité d'un article dans le cache en mémoire.

        Utilisé lors d'une mise à jour manuelle du stock réel depuis l'UI.

        :param chemin: Liste de clés JSON vers l'article.
        :param valeur: Nouvelle valeur entière de la quantité.
        :return: True si l'opération a réussi, False sinon.
        """
        try:
            ref = self._stock_cache
            for key in chemin[:-1]:
                ref = ref[key]
            elem = ref[chemin[-1]]
            if "Quantité" not in elem:
                return False
            elem["Quantité"] = valeur
            if valeur == 0:
                elem["OutOfStock"] = True
            elif valeur > 0 and elem.get("OutOfStock", False):
                elem["OutOfStock"] = False
            return True
        except (KeyError, TypeError):
            return False

    @property
    def data(self):
        """Retourne le dict de stock en mémoire (lecture directe, non copié)."""
        return self._stock_cache


# ── Singleton et réconciliation au démarrage ──────────────────────────────────

_stock_cache_instance = None


def _reconcilier_brouillons(cache: StockCache) -> None:
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


def get_stock_cache() -> StockCache:
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
        _stock_cache_instance = StockCache(str(get_stock_file_path()))
        _reconcilier_brouillons(_stock_cache_instance)
    return _stock_cache_instance
