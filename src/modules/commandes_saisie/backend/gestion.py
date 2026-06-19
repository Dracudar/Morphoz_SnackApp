#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gestion.py

Description:
    Validation des commandes et impression des tickets récapitulatif et cuisine.

Author :
    Dracudar

Version:
    2.7

Date de création :
    2026.06.02

Date de modification:
    2026.06.19
"""

import os
from datetime import datetime
from ....backend import file_io
from ....backend.commandes_utils import (
    acceder_commande,
    charger_fichier_commande,
    decrementer_ID_commande,
    get_id_cache,
    restaurer_stock_plat,
    sauvegarder_fichier_commande,
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
    with acceder_commande(chemin_fichier) as commande:
        if not commande:
            return
        commande["Informations"]["Prioritaire"] = valeur


def valider_commande(chemin_fichier):
    """
    Valide la commande : enregistre la date, imprime les tickets, passe les plats en préparation et déplace le fichier.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    """
    with acceder_commande(chemin_fichier) as commande:
        if not commande:
            return

        now = datetime.now()
        commande["Informations"]["Date de validation"] = [now.strftime("%d/%m/%Y"), now.strftime("%H:%M")]

        print_ticket_recap(chemin_fichier)
        print_ticket_cuisine(chemin_fichier)

        commande["Informations"]["Statut"] = "Validée"
        for plat in commande["Commande"].values():
            if plat["Statut"] == "En attente":
                plat["Statut"] = "En préparation"

    get_stock_cache().save()
    logger.log(logger.PERSISTANCE_STOCK, {
        "contexte": "validation_commande",
        "id_commande": commande["Informations"]["ID"],
    })

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
    deplacer = False
    with acceder_commande(chemin_fichier) as commande:
        if not commande:
            return
        plats = commande["Commande"].values()
        if all(plat["Statut"] == "Annulé" for plat in plats):
            commande["Informations"]["Statut"] = "Annulée"
            deplacer = True

    if deplacer:
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

    Verrouille le fichier pendant la lecture/modification, mais relâche le
    verrou avant d'appeler `annuler_commande` (qui verrouille lui-même le même
    fichier) pour éviter un blocage mutuel.
    """
    verifier_annulation_commande = False

    with file_io.verrou_fichier(chemin_fichier):
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
            sauvegarder_fichier_commande(chemin_fichier, commande_data)

        else:
            # --- Branche commande validée : marquage "Annulé" ---
            id_commande = commande_data["Informations"]["ID"]
            if plat["Statut"] in ("En attente", "En préparation"):
                restaurer_stock_plat(plat)
                log_stock_restauration(plat, id_commande)
                get_stock_cache().save()
                logger.log(logger.PERSISTANCE_STOCK, {
                    "contexte": "annulation_plat",
                    "id_commande": id_commande,
                })

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
            sauvegarder_fichier_commande(chemin_fichier, commande_data)
            verifier_annulation_commande = True

    if verifier_annulation_commande:
        annuler_commande(chemin_fichier)

def annuler_all_plats(chemin_fichier):
    """
    Annule tous les plats de la commande en cours.

    - Commande "En saisie" : restaure le stock, décrémente les compteurs en mémoire
      (traitement en ordre inverse pour minimiser les trous), supprime le fichier.
    - Commande validée : appelle annuler_plat pour chaque plat (comportement existant).

    Comme `annuler_plat`, relâche le verrou avant d'appeler `annuler_plat` en boucle.
    """
    with file_io.verrou_fichier(chemin_fichier):
        commande_data = charger_fichier_commande(chemin_fichier)
        if not commande_data:
            return

        statut_commande = commande_data["Informations"]["Statut"]

        if statut_commande == "En saisie":
            id_commande = commande_data["Informations"]["ID"]
            nb_plats = len(commande_data["Commande"])
            for plat in commande_data["Commande"].values():
                if plat["Statut"] == "En attente":
                    restaurer_stock_plat(plat)
                    log_stock_restauration(plat, id_commande)

            logger.log(logger.ANNULATION_COMMANDE, {
                "id_commande": id_commande,
                "nb_plats": nb_plats,
                "contexte": "saisie",
            })

            os.remove(chemin_fichier)
            decrementer_ID_commande()
            return

        plat_ids = list(commande_data["Commande"].keys())

    for plat_id in plat_ids:
        annuler_plat(chemin_fichier, plat_id)
