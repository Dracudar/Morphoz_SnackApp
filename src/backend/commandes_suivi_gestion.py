'''
Gestion des changements de statut des plats dans une commande validée.
'''

import os
import json
from datetime import datetime
from .commandes_utils import charger_fichier_commande

def plat_prêt(chemin_fichier, plat_id_complet, affichage_commandes_validées, context, frame_droite_haut):
    """
    Change le statut d'un plat de "En préparation" à "Prêt" et rafraîchit l'affichage.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    :param plat_id_complet: Identifiant complet du plat (aaaammjj-000-00).
    :param affichage_commandes_validées: Fonction pour rafraîchir l'affichage des commandes validées.
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return

    # Extraire le numéro de plat (ex. #00) à partir de l'ID complet
    numero_plat = f"#{plat_id_complet.split('-')[-1]}"

    # Vérifier si le plat existe et est en préparation
    if numero_plat in commande_data["Commande"] and commande_data["Commande"][numero_plat]["Statut"] == "En préparation":
        # Mettre à jour le statut du plat
        commande_data["Commande"][numero_plat]["Statut"] = "Prêt"

        # Remplir la date et l'heure de mise en livraison
        commande_data["Commande"][numero_plat]["Date de mise en livraison"] = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]

        # TODO: Intégrer un système d'envoi de SMS pour prévenir que le plat est prêt
        # Exemple : envoyer_sms(commande_data["Informations"]["Contact"], f"Votre plat {commande_data['Commande'][numero_plat]['Nom']} est prêt !")

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande_data, fichier, indent=4, ensure_ascii=False)

        # Rafraîchir l'affichage
        affichage_commandes_validées(context, frame_droite_haut)

def livrer_plat(chemin_fichier, plat_id_complet, affichage_commandes_validées, context, frame_droite_haut):
    """
    Change le statut d'un plat de "Prêt" à "Livré", remplit la date de livraison,
    exécute la commande terminer_commande et rafraîchit l'affichage.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    :param plat_id_complet: Identifiant complet du plat (aaaammjj-000-00).
    :param affichage_commandes_validées: Fonction pour rafraîchir l'affichage des commandes validées.
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return

    # Extraire le numéro de plat (ex. #00) à partir de l'ID complet
    numero_plat = f"#{plat_id_complet.split('-')[-1]}"

    # Vérifier si le plat existe et est prêt
    if numero_plat in commande_data["Commande"] and commande_data["Commande"][numero_plat]["Statut"] == "Prêt":
        # Mettre à jour le statut du plat
        commande_data["Commande"][numero_plat]["Statut"] = "Livré"

        # Remplir la date et l'heure de livraison
        commande_data["Commande"][numero_plat]["Date de livraison"] = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande_data, fichier, indent=4, ensure_ascii=False)

        # Exécuter la commande terminer_commande
        terminer_commande(chemin_fichier)

        # Rafraîchir l'affichage
        affichage_commandes_validées(context, frame_droite_haut)

def terminer_commande(chemin_fichier):
    """
    Termine une commande si tous les plats (hors annulés) sont livrés.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    """
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        return

    # Vérifier si tous les plats (hors annulés) sont livrés
    plats = commande["Commande"].values()
    if all(plat["Statut"] in ["Livré", "Annulé"] for plat in plats):
        # Modifier le statut de la commande
        commande["Informations"]["Statut"] = "Terminée"

        # Trouver la date et l'heure de livraison du dernier plat livré
        dernier_livraison = max(
            (plat["Date de livraison"] for plat in plats if plat["Statut"] == "Livré"),
            default=["", ""]
        )
        commande["Informations"]["Date de livraison"] = dernier_livraison

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

        # Déplacer le fichier dans le dossier "terminee"
        dossier_terminee = os.path.join(
            os.path.dirname(os.path.dirname(chemin_fichier)), "terminee"
        )
        os.makedirs(dossier_terminee, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_terminee, os.path.basename(chemin_fichier)))