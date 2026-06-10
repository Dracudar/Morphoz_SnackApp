#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gestion.py

Description:
    Validation des commandes et impression des tickets récapitulatif et cuisine.

Author :
    Dracudar

Version:
    2.4

Date de création :
    2026.06.02

Date de modification:
    2026.06.10
"""

import os
import json
from datetime import datetime
from ....backend.commandes_utils import (
    charger_fichier_commande,
    decrementer_ID_commande,
    decrementer_ID_plat,
    get_id_cache,
    restaurer_stock_plat,
    log_stock_restauration,
)
from ....backend.printer import print_ticket_recap, print_ticket_cuisine
from ....backend.data_sources import get_stock_cache
from ....backend import logger


def set_prioritaire(chemin_fichier: str, valeur: bool):
    """
    Définit le statut prioritaire d'une commande en brouillon.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    :param valeur: True pour marquer prioritaire, False pour désactiver.
    """
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        return
    commande["Informations"]["Prioritaire"] = valeur
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande, f, indent=4, ensure_ascii=False)


def valider_commande(chemin_fichier):
    """
    Valide la commande : enregistre la date, imprime les tickets, passe les plats en préparation et déplace le fichier.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    """
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        return

    # TODO : mettre en place le système de paiement (CB, espèces, repas gratuits) et mettre à jour le type de paiement dans le fichier JSON

    now = datetime.now()
    commande["Informations"]["Date de validation"] = [now.strftime("%d/%m/%Y"), now.strftime("%H:%M")]

    print_ticket_recap(chemin_fichier)
    print_ticket_cuisine(chemin_fichier)

    commande["Informations"]["Statut"] = "Validée"
    for plat in commande["Commande"].values():
        if plat["Statut"] == "En attente":
            plat["Statut"] = "En préparation"

    # TODO : Mettre en place un système d'impression de ticket de commande
    # 1 ticket par plat mis en préparation avec l'ID complet, le nom du plat et la composition
    # 1 ticket récapitulatif avec l'ID de la commande, le montant total, le type de paiement et la date de validation, la liste des plats mis en préparation (numéro de plat et nom du plat)

    with open(chemin_fichier, "w", encoding="utf-8") as fichier:
        json.dump(commande, fichier, indent=4, ensure_ascii=False)

    get_stock_cache().save()
    logger.log(logger.PERSISTANCE_STOCK, {
        "contexte": "validation_commande",
        "id_commande": commande["Informations"]["ID"],
    })
    get_id_cache().save()

    logger.log(logger.VALIDATION_COMMANDE, {
        "id_commande": commande["Informations"]["ID"],
        "montant": commande["Informations"]["Montant"],
        "nb_plats": len(commande["Commande"]),
        "prioritaire": commande["Informations"].get("Prioritaire", False),
    })

    dossier_en_cours = os.path.join(os.path.dirname(chemin_fichier), "en_cours")
    os.makedirs(dossier_en_cours, exist_ok=True)
    os.rename(chemin_fichier, os.path.join(dossier_en_cours, os.path.basename(chemin_fichier)))

# == Annulation de commande == #
def annuler_commande(chemin_fichier):
    """
    Pour une commande validée : marque la commande "Annulée" et déplace le fichier
    dès que tous ses plats sont à l'état "Annulé".

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    """
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        return

    plats = commande["Commande"].values()
    if all(plat["Statut"] == "Annulé" for plat in plats):
        commande["Informations"]["Statut"] = "Annulée"

        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

        dossier_annulee = os.path.join(os.path.dirname(chemin_fichier), "annulee")
        os.makedirs(dossier_annulee, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_annulee, os.path.basename(chemin_fichier)))


def annuler_plat(chemin_fichier, plat_id):
    """
    Annule un plat dans la commande en cours.

    - Commande "En saisie" + plat "En attente" : suppression physique du plat et
      décrémentation du compteur de type en mémoire. La clé type (P001, G001…)
      est supprimée directement, sans renumérotation.
      Si la commande devient vide, le fichier est supprimé.
    - Commande validée : marquage "Annulé" et déplacement si tous les plats
      sont annulés (comportement existant).
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return

    # Résoudre la clé : accepte la clé directe ("P001") ou l'ID complet ("20260607-097-P001")
    plat_key = plat_id if plat_id in commande_data["Commande"] else next(
        (k for k, v in commande_data["Commande"].items() if v.get("ID") == plat_id),
        None
    )
    if plat_key is None:
        return

    plat = commande_data["Commande"][plat_key]
    statut_commande = commande_data["Informations"]["Statut"]

    if statut_commande == "En saisie" and plat["Statut"] == "En attente":
        # --- Branche saisie : suppression physique ---
        id_commande = commande_data["Informations"]["ID"]
        restaurer_stock_plat(plat)
        log_stock_restauration(plat, id_commande)
        # La clé IS déjà le type part (ex: "P030") — pas besoin de l'extraire de l'ID
        decrementer_ID_plat(plat.get("Plat", ""), plat_key)

        logger.log(logger.ANNULATION_PLAT, {
            "id_commande": id_commande,
            "id_plat": plat.get("ID", plat_key),
            "type_plat": plat.get("Plat", ""),
            "nom_plat": plat.get("Nom", ""),
            "contexte": "saisie",
        })

        del commande_data["Commande"][plat_key]

        if not commande_data["Commande"]:
            os.remove(chemin_fichier)
            decrementer_ID_commande()
            return

        commande_data["Informations"]["Montant"] = sum(
            p["Prix"] for p in commande_data["Commande"].values()
        )

        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande_data, f, indent=4, ensure_ascii=False)

    else:
        # --- Branche commande validée : marquage "Annulé" ---
        id_commande = commande_data["Informations"]["ID"]
        if plat["Statut"] in ("En attente", "En préparation"):
            restaurer_stock_plat(plat)
            log_stock_restauration(plat, id_commande)

        logger.log(logger.ANNULATION_PLAT, {
            "id_commande": id_commande,
            "id_plat": plat.get("ID", plat_key),
            "type_plat": plat.get("Plat", ""),
            "nom_plat": plat.get("Nom", ""),
            "contexte": "commande_validee",
        })

        plat["Statut"] = "Annulé"

        commande_data["Informations"]["Montant"] = sum(
            p["Prix"] for p in commande_data["Commande"].values() if p["Statut"] != "Annulé"
        )

        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande_data, f, indent=4, ensure_ascii=False)

        annuler_commande(chemin_fichier)

def annuler_all_plats(chemin_fichier):
    """
    Annule tous les plats de la commande en cours.

    - Commande "En saisie" : restaure le stock, décrémente les compteurs en mémoire
      (traitement en ordre inverse pour minimiser les trous), supprime le fichier.
    - Commande validée : appelle annuler_plat pour chaque plat (comportement existant).
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return

    statut_commande = commande_data["Informations"]["Statut"]

    if statut_commande == "En saisie":
        id_commande = commande_data["Informations"]["ID"]
        nb_plats = len(commande_data["Commande"])
        # Traitement en ordre inverse (tri alpha-numérique décroissant) pour maximiser
        # les décrémentations consécutives et éviter les trous
        for plat_key in sorted(commande_data["Commande"], reverse=True):
            plat = commande_data["Commande"][plat_key]
            if plat["Statut"] == "En attente":
                restaurer_stock_plat(plat)
                log_stock_restauration(plat, id_commande)
                decrementer_ID_plat(plat.get("Plat", ""), plat_key)

        logger.log(logger.ANNULATION_COMMANDE, {
            "id_commande": id_commande,
            "nb_plats": nb_plats,
            "contexte": "saisie",
        })

        os.remove(chemin_fichier)
        decrementer_ID_commande()

    else:
        plat_ids = list(commande_data["Commande"].keys())
        for plat_id in plat_ids:
            annuler_plat(chemin_fichier, plat_id)
