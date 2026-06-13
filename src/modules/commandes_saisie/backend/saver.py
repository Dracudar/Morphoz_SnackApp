#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
saver.py

Description:
    Création et mise à jour du fichier JSON de la commande en cours de saisie.

Author :
    Dracudar

Version:
    3.0

Date de création :
    2026.06.02

Date de modification:
    2026.06.08
"""

import os
import json
from datetime import datetime
from collections import OrderedDict
from src.backend.commandes_utils import (
    charger_fichier_commande,
    generer_ID_commande,
    generer_ID_plat,
)
from src.backend import logger


def initialiser_dossiers_commandes(commandes_path, logs_path):
    """
    Crée la structure de dossiers nécessaire pour l'enregistrement des commandes.
    Appelée avant chaque sauvegarde pour garantir l'existence des dossiers.

    :param commandes_path: Chemin vers le dossier des commandes
    :param logs_path: Chemin vers le dossier des logs
    """
    for chemin, type_dossier in [
        (logs_path, "logs"),
        (commandes_path, "commandes"),
        (os.path.join(commandes_path, "en_cours"), "commandes/en_cours"),
        (os.path.join(commandes_path, "terminee"), "commandes/terminee"),
        (os.path.join(commandes_path, "annulee"), "commandes/annulee"),
        (os.path.join(commandes_path, "corrompu"), "commandes/corrompu"),
    ]:
        creation = not os.path.exists(chemin)
        os.makedirs(chemin, exist_ok=True)
        if creation:
            logger.log(logger.CREATION_DOSSIER, {"chemin": chemin, "type": type_dossier})


# === Gestion des fichiers de commandes === #
def creer_dict_plat(plat_id, plat):
    """
    Crée un dictionnaire représentant un plat.
    L'identifiant plat_id est au format aaaammjj-000-X000 (ex: 20260606-007-P030).
    Le champ 'Recette' est inséré après 'Plat' pour les pizzas.
    """
    base_dict = {
        "ID": plat_id,
        "Plat": plat["Plat"],
        "Nom": plat["Nom"],
        "Date de mise en livraison": ["", ""],
        "Date de livraison": ["", ""],
        "Date d'annulation": ["", ""],
        "Statut": "En attente",
        "Prix": plat["Prix"],
        "Composition": plat["Composition"]
    }
    if plat["Plat"].lower() == "pizza":
        # Réorganiser pour insérer "Recette" entre "Plat" et "Nom"
        return OrderedDict([
            ("ID", base_dict["ID"]),
            ("Plat", base_dict["Plat"]),
            ("Recette", plat.get("Recette", "")),
            ("Nom", base_dict["Nom"]),
            ("Date de mise en livraison", base_dict["Date de mise en livraison"]),
            ("Date de livraison", base_dict["Date de livraison"]),
            ("Date d'annulation", base_dict["Date d'annulation"]),
            ("Statut", base_dict["Statut"]),
            ("Prix", base_dict["Prix"]),
            ("Composition", base_dict["Composition"]),
        ])
    else:
        return base_dict

def _sort_key_plat(id_type: str) -> tuple:
    """Retourne (lettre, numéro) pour trier les plats comme à l'affichage. Ex: 'P030' → ('P', 30)."""
    if id_type and len(id_type) > 1 and id_type[0].isalpha():
        try:
            return (id_type[0], int(id_type[1:]))
        except ValueError:
            pass
    return ("", 0)


def _log_stock_ajout(plat: dict, plat_id: str, id_commande: str) -> None:
    """Log les modifications automatiques de stock lors de l'ajout d'un plat."""
    type_plat = plat.get("Plat", "")
    if type_plat == "Pizza":
        logger.log(logger.MODIFICATION_CACHE_STOCK, {
            "raison": "ajout_plat",
            "id_commande": id_commande,
            "id_plat": plat_id,
            "type_plat": "Pizza",
            "nom_plat": plat.get("Nom", ""),
            "modifications": [{"chemin": ["Plats", "Pizza", "Pâte à pizza"], "delta": -1}],
        })
    elif type_plat == "Grillade":
        viandes = plat.get("Composition", {}).get("Viandes", {})
        if viandes:
            logger.log(logger.MODIFICATION_CACHE_STOCK, {
                "raison": "ajout_plat",
                "id_commande": id_commande,
                "id_plat": plat_id,
                "type_plat": "Grillade",
                "nom_plat": plat.get("Nom", ""),
                "modifications": [
                    {"chemin": ["Plats", "Grillades", viande], "delta": -qte}
                    for viande, qte in viandes.items()
                ],
            })


def MAJ_commande(commandes_path, logs_path, plat):
    """
    Ajoute un plat à une commande existante ou crée une nouvelle commande.
    L'identifiant du plat est construit en combinant l'ID de commande et
    l'identifiant journalier de type (ex: 20260606-007-P030).

    :param commandes_path: Chemin vers le dossier des commandes.
    :param logs_path: Chemin vers le dossier des logs.
    :param plat: Dictionnaire contenant les informations du plat à ajouter.
    """
    initialiser_dossiers_commandes(commandes_path, logs_path)

    fichiers_commandes = [
        f for f in os.listdir(commandes_path) if f.startswith("commande_") and f.endswith(".json")
    ]

    if fichiers_commandes:
        fichiers_commandes.sort()
        chemin_fichier = os.path.join(commandes_path, fichiers_commandes[-1])

        commande = charger_fichier_commande(chemin_fichier)
        if not commande:
            return

        id_type = generer_ID_plat(plat["Plat"])  # ex: "P030"
        plat_id = f"{commande['Informations']['ID']}-{id_type}"  # ex: "20260606-007-P030"
        commande["Commande"][id_type] = creer_dict_plat(plat_id, plat)

        commande["Informations"]["Montant"] = sum(
            p["Prix"] for p in commande["Commande"].values() if p["Statut"] != "Annulé"
        )

        # Trier les plats par type alphabétique puis numéro croissant (ex: B001 < G001 < P001)
        commande["Commande"] = dict(
            sorted(commande["Commande"].items(), key=lambda kv: _sort_key_plat(kv[0]))
        )

        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

        logger.log(logger.AJOUT_PLAT, {
            "id_commande": commande["Informations"]["ID"],
            "id_plat": plat_id,
            "type_plat": plat["Plat"],
            "nom_plat": plat["Nom"],
            "prix": plat["Prix"],
        })
        _log_stock_ajout(plat, plat_id, commande["Informations"]["ID"])

    else:
        nouvel_id = generer_ID_commande()
        chemin_fichier = os.path.join(commandes_path, f"commande_{nouvel_id}.json")
        id_type = generer_ID_plat(plat["Plat"])  # ex: "P001"
        plat_id = f"{nouvel_id}-{id_type}"  # ex: "20260606-007-P001"
        nouvelle_commande = {
            "Informations": {
                "ID": nouvel_id,
                "Date de création": [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")],
                "Date de validation": ["", ""],
                "Date de finalisation": ["", ""],
                "Date d'annulation": ["", ""],
                "Statut": "En saisie",
                "Montant": plat["Prix"],
                "Devise": "EUR",
                "Type de paiement": "",
                "Prioritaire": False,
                "Contact": ""
            },
            "Commande": {
                id_type: creer_dict_plat(plat_id, plat)
            }
        }

        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(nouvelle_commande, fichier, indent=4, ensure_ascii=False)

        logger.log(logger.AJOUT_PLAT, {
            "id_commande": nouvel_id,
            "id_plat": plat_id,
            "type_plat": plat["Plat"],
            "nom_plat": plat["Nom"],
            "prix": plat["Prix"],
        })
        _log_stock_ajout(plat, plat_id, nouvel_id)
