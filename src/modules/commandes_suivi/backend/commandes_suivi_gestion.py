#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
commandes_suivi_gestion.py

Description:
    Gestion des changements de statut des plats dans les commandes validées.

Author :
    Dracudar

Version:
    1.4

Date de création :
    2025.05.31

Date de modification:
    2026.06.10
"""

import json
import os
from datetime import datetime
from src.backend.commandes_utils import (
    charger_fichier_commande,
    restaurer_stock_plat,
    log_stock_restauration,
    trouver_candidat_transfert,
)
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
    Termine une commande si tous les plats (hors annulés) sont livrés ou non livrés.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    """
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        return

    plats = list(commande["Commande"].values())
    etats_terminaux = {"Livré", "Annulé", "Non livré"}
    if all(plat["Statut"] in etats_terminaux for plat in plats):
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
            "nb_plats_non_livres": sum(1 for p in plats if p["Statut"] == "Non livré"),
        })

        dossier_terminee = os.path.join(
            os.path.dirname(os.path.dirname(chemin_fichier)), "terminee"
        )
        os.makedirs(dossier_terminee, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_terminee, os.path.basename(chemin_fichier)))


# ── Actions depuis l'historique (sans callback de rafraîchissement) ───────────

def marquer_plat_pret(chemin_fichier: str, plat_id_complet: str) -> bool:
    """Change le statut d'un plat de "En préparation" à "Prêt" avec horodatage."""
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return False
    plat_key = _trouver_cle_plat(commande_data, plat_id_complet)
    if not plat_key or commande_data["Commande"][plat_key]["Statut"] != "En préparation":
        return False
    plat_data = commande_data["Commande"][plat_key]
    now = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]
    commande_data["Commande"][plat_key]["Statut"] = "Prêt"
    commande_data["Commande"][plat_key]["Date de mise en livraison"] = now
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande_data, f, indent=4, ensure_ascii=False)
    logger.log(logger.PLAT_PRET, {
        "id_commande": commande_data["Informations"]["ID"],
        "id_plat": plat_id_complet,
        "type_plat": plat_data.get("Plat", ""),
        "nom_plat": plat_data.get("Nom", ""),
        "contexte": "historique",
    })
    return True


def marquer_plat_livre(chemin_fichier: str, plat_id_complet: str) -> bool:
    """Change le statut d'un plat (En préparation ou Prêt) à "Livré". Termine la commande si tous les plats sont traités."""
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return False
    plat_key = _trouver_cle_plat(commande_data, plat_id_complet)
    if not plat_key or commande_data["Commande"][plat_key]["Statut"] not in ("En préparation", "Prêt"):
        return False
    plat_data = commande_data["Commande"][plat_key]
    now = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]
    commande_data["Commande"][plat_key]["Statut"] = "Livré"
    commande_data["Commande"][plat_key]["Date de livraison"] = now
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande_data, f, indent=4, ensure_ascii=False)
    logger.log(logger.PLAT_LIVRE, {
        "id_commande": commande_data["Informations"]["ID"],
        "id_plat": plat_id_complet,
        "type_plat": plat_data.get("Plat", ""),
        "nom_plat": plat_data.get("Nom", ""),
        "contexte": "historique",
    })
    terminer_commande(chemin_fichier)
    return True


def _marquer_non_livre(commande_data: dict, plat_key: str, chemin_fichier: str) -> None:
    """Marque un plat "Non livré" avec horodatage et sauvegarde."""
    plat_data = commande_data["Commande"][plat_key]
    now = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]
    commande_data["Commande"][plat_key]["Statut"] = "Non livré"
    commande_data["Commande"][plat_key]["Date d'annulation"] = now
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande_data, f, indent=4, ensure_ascii=False)
    logger.log(logger.PLAT_NON_LIVRE, {
        "id_commande": commande_data["Informations"]["ID"],
        "id_plat": plat_data.get("ID", ""),
        "type_plat": plat_data.get("Plat", ""),
        "nom_plat": plat_data.get("Nom", ""),
        "contexte": "historique",
    })


def _transferer_pret(plat_data: dict, chemin_source: str) -> bool:
    """
    Tente de transférer l'état "Prêt" au prochain plat identique "En préparation".

    Retourne True si le transfert a eu lieu, False sinon.
    """
    candidat = trouver_candidat_transfert(plat_data, chemin_source)
    if candidat is None:
        return False

    chemin_dest, plat_id_dest = candidat
    commande_dest = charger_fichier_commande(chemin_dest)
    if not commande_dest:
        return False

    plat_key_dest = _trouver_cle_plat(commande_dest, plat_id_dest)
    if not plat_key_dest:
        return False

    now = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]
    commande_dest["Commande"][plat_key_dest]["Statut"] = "Prêt"
    commande_dest["Commande"][plat_key_dest]["Date de mise en livraison"] = now
    with open(chemin_dest, "w", encoding="utf-8") as f:
        json.dump(commande_dest, f, indent=4, ensure_ascii=False)

    logger.log(logger.TRANSFERT_PRET, {
        "id_commande_source": commande_dest["Informations"].get("ID", ""),
        "id_plat_dest": plat_id_dest,
        "type_plat": plat_data.get("Plat", ""),
        "nom_plat": plat_data.get("Nom", ""),
        "contexte": "historique",
    })
    return True


def annuler_plat_valide(chemin_fichier: str, plat_id_complet: str) -> bool:
    """
    Annule un plat d'une commande validée avec horodatage.

    Comportement selon le statut du plat :
    - "En préparation" : restaure le stock (ingrédients non encore cuisinés), marque "Annulé".
    - "Prêt"           : le plat est physiquement prêt ; cherche un plat identique "En préparation"
                         dans les commandes actives et lui transfère le statut "Prêt". Si aucun
                         candidat n'est trouvé, marque le plat "Non livré" (perte).
    - Autre statut actif : marque "Annulé" sans action stock.

    Finalise la commande si tous les plats sont dans un état terminal.
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return False
    plat_key = _trouver_cle_plat(commande_data, plat_id_complet)
    if not plat_key or commande_data["Commande"][plat_key]["Statut"] in ("Annulé", "Livré", "Non livré"):
        return False

    plat_data = commande_data["Commande"][plat_key]
    id_commande = commande_data["Informations"]["ID"]
    statut_plat = plat_data["Statut"]
    now = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]

    if statut_plat == "En préparation":
        restaurer_stock_plat(plat_data)
        log_stock_restauration(plat_data, id_commande)
        commande_data["Commande"][plat_key]["Statut"] = "Annulé"
        commande_data["Commande"][plat_key]["Date d'annulation"] = now
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande_data, f, indent=4, ensure_ascii=False)
        logger.log(logger.ANNULATION_PLAT, {
            "id_commande": id_commande,
            "id_plat": plat_id_complet,
            "type_plat": plat_data.get("Plat", ""),
            "nom_plat": plat_data.get("Nom", ""),
            "contexte": "historique",
        })

    elif statut_plat == "Prêt":
        # Le plat est physiquement prêt : tenter un transfert vers un plat identique en préparation
        transfere = _transferer_pret(plat_data, chemin_fichier)
        # Recharger après que le transfert a pu modifier le fichier source (même commande)
        commande_data = charger_fichier_commande(chemin_fichier)
        if not commande_data:
            return False
        plat_key = _trouver_cle_plat(commande_data, plat_id_complet)
        if not plat_key:
            return False
        if transfere:
            commande_data["Commande"][plat_key]["Statut"] = "Annulé"
            commande_data["Commande"][plat_key]["Date d'annulation"] = now
            with open(chemin_fichier, "w", encoding="utf-8") as f:
                json.dump(commande_data, f, indent=4, ensure_ascii=False)
            logger.log(logger.ANNULATION_PLAT, {
                "id_commande": id_commande,
                "id_plat": plat_id_complet,
                "type_plat": plat_data.get("Plat", ""),
                "nom_plat": plat_data.get("Nom", ""),
                "contexte": "historique",
            })
        else:
            _marquer_non_livre(commande_data, plat_key, chemin_fichier)

    else:
        commande_data["Commande"][plat_key]["Statut"] = "Annulé"
        commande_data["Commande"][plat_key]["Date d'annulation"] = now
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande_data, f, indent=4, ensure_ascii=False)
        logger.log(logger.ANNULATION_PLAT, {
            "id_commande": id_commande,
            "id_plat": plat_id_complet,
            "type_plat": plat_data.get("Plat", ""),
            "nom_plat": plat_data.get("Nom", ""),
            "contexte": "historique",
        })

    _finaliser_apres_annulation(chemin_fichier)
    return True


def annuler_commande_complete(chemin_fichier: str) -> bool:
    """
    Annule tous les plats actifs d'une commande validée avec horodatage.

    Applique la même logique que l'annulation unitaire :
    - "En préparation" : restaure le stock, marque "Annulé".
    - "Prêt"           : tente un transfert vers un plat identique, sinon "Non livré".
    - Déjà terminal ("Annulé", "Livré", "Non livré") : ignoré.
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return False

    # Collecter les IDs des plats à traiter avant de modifier le fichier
    plats_a_traiter = [
        plat.get("ID", "")
        for plat in commande_data["Commande"].values()
        if plat["Statut"] not in ("Annulé", "Livré", "Non livré")
    ]
    if not plats_a_traiter:
        return False

    nb_annules = 0
    for plat_id in plats_a_traiter:
        annuler_plat_valide(chemin_fichier, plat_id)
        nb_annules += 1

    logger.log(logger.ANNULATION_COMMANDE, {
        "id_commande": commande_data["Informations"]["ID"],
        "nb_plats_annules": nb_annules,
        "contexte": "historique",
    })
    return True


def _finaliser_apres_annulation(chemin_fichier: str):
    """Vérifie si tous les plats sont dans un état terminal et finalise la commande en conséquence."""
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        return
    plats = list(commande["Commande"].values())
    etats_terminaux = {"Annulé", "Livré", "Non livré"}
    if not all(p["Statut"] in etats_terminaux for p in plats):
        return
    if all(p["Statut"] == "Annulé" for p in plats):
        # Tous strictement annulés : commande annulée
        now = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]
        commande["Informations"]["Statut"] = "Annulée"
        commande["Informations"]["Date d'annulation"] = now
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande, f, indent=4, ensure_ascii=False)
        dossier_annulee = os.path.join(os.path.dirname(os.path.dirname(chemin_fichier)), "annulee")
        os.makedirs(dossier_annulee, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_annulee, os.path.basename(chemin_fichier)))
    else:
        # Mélange livré + annulé + non livré : commande terminée
        terminer_commande(chemin_fichier)
