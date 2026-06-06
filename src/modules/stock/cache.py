#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cache.py

Description:
    Cache en mémoire pour les données de stock, avec comparaison aux valeurs originales pour détecter les modifications.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2025.06.17

Date de modification:
    2026.06.06
"""

import copy
import json

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

    @property
    def data(self):
        """Retourne le dict de stock en mémoire (lecture directe, non copié)."""
        return self._stock_cache