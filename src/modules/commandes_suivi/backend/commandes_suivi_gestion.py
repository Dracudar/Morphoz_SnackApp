#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
commandes_suivi_gestion.py

Description:
    Gestion des changements de statut des plats dans les commandes validées.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2025.05.31

Date de modification:
    2026.06.06
"""

import os
import json
from datetime import datetime
from src.backend.commandes_utils import charger_fichier_commande
from src.backend import logger


def _trouver_cle_plat(commande_data: dict, plat_id_complet: str):
    """
    Retourne la clé JSON (#01, #02…) du plat correspondant à plat_id_complet,
    en cherchant par valeur du champ ID (format aaaammjj-000-X000).
    """
    return next(
        (k for k, v in commande_data["Commande"].items() if v.get("ID") == plat_id_complet),
        None
    )


def plat_prêt(context, chemin_fichier, plat_id_complet, affichage_commandes_validées):
    """
    Change le statut d'un plat de "En préparation" à "Prêt" et rafraîchit l'affichage.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    :param plat_id_complet: Identifiant complet du plat (aaaammjj-000-X000).
    :param affichage_commandes_validées: Fonction pour rafraîchir l'affichage des commandes validées.
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return

    plat_key = _trouver_cle_plat(commande_data, plat_id_complet)
    if plat_key and commande_data["Commande"][plat_key]["Statut"] == "En préparation":
        plat_data = commande_data["Commande"][plat_key]
        commande_data["Commande"][plat_key]["Statut"] = "Prêt"
        commande_data["Commande"][plat_key]["Date de mise en livraison"] = [
            datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
        ]

        # TODO: Intégrer un système d'envoi de SMS pour prévenir que le plat est prêt

        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande_data, fichier, indent=4, ensure_ascii=False)

        logger.log(logger.PLAT_PRET, {
            "id_commande": commande_data["Informations"]["ID"],
            "id_plat": plat_id_complet,
            "type_plat": plat_data.get("Plat", ""),
            "nom_plat": plat_data.get("Nom", ""),
        })

        affichage_commandes_validées(context)

def livrer_plat(context, chemin_fichier, plat_id_complet, affichage_commandes_validées):
    """
    Change le statut d'un plat de "Prêt" à "Livré", remplit la date de livraison,
    exécute la commande terminer_commande et rafraîchit l'affichage.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    :param plat_id_complet: Identifiant complet du plat (aaaammjj-000-X000).
    :param affichage_commandes_validées: Fonction pour rafraîchir l'affichage des commandes validées.
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return

    plat_key = _trouver_cle_plat(commande_data, plat_id_complet)
    if plat_key and commande_data["Commande"][plat_key]["Statut"] == "Prêt":
        plat_data = commande_data["Commande"][plat_key]
        commande_data["Commande"][plat_key]["Statut"] = "Livré"
        commande_data["Commande"][plat_key]["Date de livraison"] = [
            datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")
        ]

        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande_data, fichier, indent=4, ensure_ascii=False)

        logger.log(logger.PLAT_LIVRE, {
            "id_commande": commande_data["Informations"]["ID"],
            "id_plat": plat_id_complet,
            "type_plat": plat_data.get("Plat", ""),
            "nom_plat": plat_data.get("Nom", ""),
        })

        terminer_commande(chemin_fichier)
        affichage_commandes_validées(context)

def terminer_commande(chemin_fichier):
    """
    Termine une commande si tous les plats (hors annulés) sont livrés.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    """
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        return

    plats = list(commande["Commande"].values())
    if all(plat["Statut"] in ["Livré", "Annulé"] for plat in plats):
        commande["Informations"]["Statut"] = "Terminée"

        dernier_livraison = max(
            (plat["Date de livraison"] for plat in plats if plat["Statut"] == "Livré"),
            default=["", ""]
        )
        commande["Informations"]["Date de livraison"] = dernier_livraison

        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

        logger.log(logger.COMMANDE_TERMINEE, {
            "id_commande": commande["Informations"]["ID"],
            "nb_plats_livres": sum(1 for p in plats if p["Statut"] == "Livré"),
            "nb_plats_annules": sum(1 for p in plats if p["Statut"] == "Annulé"),
        })

        dossier_terminee = os.path.join(
            os.path.dirname(os.path.dirname(chemin_fichier)), "terminee"
        )
        os.makedirs(dossier_terminee, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_terminee, os.path.basename(chemin_fichier)))
