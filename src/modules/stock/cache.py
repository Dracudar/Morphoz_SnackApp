#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cache.py

Description:
    Cache en mémoire pour les données de stock, avec comparaison aux valeurs originales pour détecter les modifications.

    Le fichier de stock est partagé par plusieurs postes sur le réseau local
    (caisse, cuisine...), chacun avec son propre cache en mémoire. Pour éviter
    qu'une sauvegarde n'écrase les décréments faits par un autre poste entre le
    chargement initial et la sauvegarde, `save()` ne réécrit pas l'état en
    mémoire tel quel : elle recharge la version la plus récente du fichier sous
    verrou et y rejoue les opérations locales (voir `save()`).

Author :
    Dracudar

Version:
    2.0

Date de création :
    2025.06.17

Date de modification:
    2026.06.19
"""

import copy

from src.backend import file_io


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
        # Opérations locales à rejouer sur l'état disque le plus récent à la sauvegarde
        # (voir save()). Chaque entrée : (action, chemin, valeur).
        self._operations = []

    def _charger_stock(self):
        """Lit et retourne le contenu du fichier JSON de stock."""
        return file_io.charger_json(self.chemin_stock_json)

    def reset_cache(self):
        """Réinitialise le cache à partir des valeurs originales chargées."""
        self._stock_cache = copy.deepcopy(self._stock_original)
        self._operations.clear()

    def save(self):
        """
        Persiste les modifications sur disque.

        Sous verrou : recharge la version la plus récente du fichier (qui peut
        avoir été modifiée par un autre poste depuis le chargement initial), y
        rejoue les opérations effectuées localement depuis le dernier save/reset,
        puis sauvegarde ce résultat fusionné. Cela évite qu'un poste écrase les
        décréments faits par un autre poste pendant le service.
        """
        with file_io.verrou_fichier(self.chemin_stock_json):
            stock_actuel = file_io.charger_json(self.chemin_stock_json)
            for operation in self._operations:
                self._rejouer_operation(stock_actuel, operation)
            file_io.sauvegarder_json(self.chemin_stock_json, stock_actuel)

        self._stock_cache = stock_actuel
        self._stock_original = copy.deepcopy(stock_actuel)
        self._operations.clear()

    @staticmethod
    def _rejouer_operation(data, operation):
        """
        Applique une opération enregistrée sur des données de stock fraîchement
        rechargées (utilisé par `save()` pour fusionner avec l'état disque actuel).

        decrementer/incrementer rejouent le delta tel quel, sans revérifier la
        quantité disponible : la consommation (ou la restitution) a déjà eu lieu
        réellement sur ce poste, revalider la disponibilité au moment de la
        fusion risquerait de perdre silencieusement une vente déjà actée.
        """
        action, chemin, valeur = operation
        ref = data
        try:
            for key in chemin[:-1]:
                ref = ref[key]
            elem = ref[chemin[-1]]
        except (KeyError, TypeError):
            return

        if action == "set_out_of_stock":
            elem["OutOfStock"] = valeur
            return

        if "Quantité" not in elem:
            return
        if action == "decrementer":
            elem["Quantité"] = max(0, elem["Quantité"] - valeur)
        elif action == "incrementer":
            elem["Quantité"] += valeur
        elif action == "set_quantite":
            elem["Quantité"] = valeur
        elem["OutOfStock"] = elem["Quantité"] <= 0

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
            self._operations.append(("decrementer", list(chemin), n))
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
            self._operations.append(("incrementer", list(chemin), n))
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
            self._operations.append(("set_out_of_stock", list(chemin), valeur))
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
            self._operations.append(("set_quantite", list(chemin), valeur))
            return True
        except (KeyError, TypeError):
            return False

    @property
    def data(self):
        """Retourne le dict de stock en mémoire (lecture directe, non copié)."""
        return self._stock_cache
