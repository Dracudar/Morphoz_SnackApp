#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stock_utils.py

Description:
    Restauration du stock à l'annulation d'un plat et chargement de fichiers
    JSON de commande avec gestion des erreurs (quarantaine des fichiers corrompus).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.16

Date de modification:
    2026.06.16
"""

import os
import json
from src.backend import logger


def restaurer_stock_plat(plat: dict) -> None:
    """Restitue dans le cache les quantités consommées par un plat annulé."""
    from src.backend.data.stock import get_stock_cache
    cache = get_stock_cache()
    plat_type = plat.get("Plat", "")
    composition = plat.get("Composition", {})
    if plat_type == "Pizza":
        cache.incrementer(["Plats", "Pizza", "Pâte à pizza"])
    elif plat_type == "Grillade":
        for viande, qte in composition.get("Viandes", {}).items():
            cache.incrementer(["Plats", "Grillades", viande], qte)


def log_stock_restauration(plat: dict, id_commande: str) -> None:
    """Log la restauration automatique de stock lors de l'annulation d'un plat."""
    type_plat = plat.get("Plat", "")
    if type_plat == "Pizza":
        logger.log(logger.MODIFICATION_CACHE_STOCK, {
            "raison": "annulation_plat",
            "id_commande": id_commande,
            "id_plat": plat.get("ID", ""),
            "type_plat": "Pizza",
            "nom_plat": plat.get("Nom", ""),
            "modifications": [{"chemin": ["Plats", "Pizza", "Pâte à pizza"], "delta": +1}],
        })
    elif type_plat == "Grillade":
        viandes = plat.get("Composition", {}).get("Viandes", {})
        if viandes:
            logger.log(logger.MODIFICATION_CACHE_STOCK, {
                "raison": "annulation_plat",
                "id_commande": id_commande,
                "id_plat": plat.get("ID", ""),
                "type_plat": "Grillade",
                "nom_plat": plat.get("Nom", ""),
                "modifications": [
                    {"chemin": ["Plats", "Grillades", viande], "delta": +qte}
                    for viande, qte in viandes.items()
                ],
            })


# ── Chargement JSON ────────────────────────────────────────────────────────────

def charger_fichier_commande(chemin_fichier):
    """
    Charge un fichier JSON avec gestion des erreurs.

    :param chemin_fichier: Chemin vers le fichier JSON.
    :return: Contenu du fichier sous forme de dictionnaire ou None si une erreur survient.
    """
    if not os.path.exists(chemin_fichier):
        print(f"Erreur : Le fichier '{chemin_fichier}' est introuvable.")
        logger.log(logger.ERREUR, {
            "contexte": "lecture_commande",
            "message": "Fichier introuvable",
            "chemin": chemin_fichier,
        })
        return None

    try:
        with open(chemin_fichier, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier '{chemin_fichier}' contient des données invalides.")
        dossier_corrompu = os.path.join(os.path.dirname(chemin_fichier), "corrompu")
        os.makedirs(dossier_corrompu, exist_ok=True)
        chemin_destination = os.path.join(dossier_corrompu, os.path.basename(chemin_fichier))
        os.rename(chemin_fichier, chemin_destination)
        logger.log(logger.FICHIER_CORROMPU, {
            "chemin_original": chemin_fichier,
            "chemin_destination": chemin_destination,
        })
        return None
