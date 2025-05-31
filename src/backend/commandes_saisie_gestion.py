'''

'''

import os
import json
from datetime import datetime
from .commandes_utils import charger_fichier_json

def valider_commande(chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
    commande = charger_fichier_json(chemin_fichier)
    if not commande:
        return

    # TODO : mettre en place le système de paiement (CB, espèces, repas gratuits) et mettre à jour le type de paiement dans le fichier JSON
    
    # Mettre à jour la date de validation
    commande["Informations"]["Date de validation"] = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]

    # Mettre à jour les statuts
    commande["Informations"]["Statut"] = "Validée"
    for plat in commande["Commande"].values():
        if plat["Statut"] == "En attente":
            plat["Statut"] = "En préparation"

    # TODO : Mettre en place un système d'impression de ticket de commande
    # 1 ticket par plat mis en préparation avec l'ID complet, le nom du plat et la composition
    # 1 ticket récapitulatif avec l'ID de la commande, le montant total, le type de paiement et la date de validation, la liste des plats mis en préparation (numéro de plat et nom du plat)

    # Sauvegarder les modifications
    with open(chemin_fichier, "w", encoding="utf-8") as fichier:
        json.dump(commande, fichier, indent=4, ensure_ascii=False)

    # Déplacer le fichier
    dossier_en_cours = os.path.join(os.path.dirname(chemin_fichier), "en_cours")
    os.makedirs(dossier_en_cours, exist_ok=True)
    os.rename(chemin_fichier, os.path.join(dossier_en_cours, os.path.basename(chemin_fichier)))

    # Rafraîchir l'affichage
    affichage_commande_actuelle()
    affichage_commandes_validées()

# == Annulation de commande == #
def annuler_commande(chemin_fichier):
    commande = charger_fichier_json(chemin_fichier)
    if not commande:
        return

    # Vérifier si tous les plats sont annulés
    plats = commande["Commande"].values()
    if all(plat["Statut"] == "Annulé" for plat in plats):
        commande["Informations"]["Statut"] = "Annulée"

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

        # Déplacer le fichier
        dossier_annulee = os.path.join(os.path.dirname(chemin_fichier), "annulee")
        os.makedirs(dossier_annulee, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_annulee, os.path.basename(chemin_fichier)))

def annuler_plat(commande_file, plat_id, chemin_fichier, affichage_commande_actuelle):
    """
    Annule un plat dans la commande en cours.
    """
    commande_data = charger_fichier_json(commande_file)
    if not commande_data:
        return

    # Mettre à jour le statut du plat
    commande_data["Commande"][plat_id]["Statut"] = "Annulé"

    # Recalculer le montant total
    commande_data["Informations"]["Montant"] = sum(
        plat["Prix"] for plat in commande_data["Commande"].values() if plat["Statut"] != "Annulé"
    )
    
    # Sauvegarder les modifications
    with open(commande_file, "w", encoding="utf-8") as f:
        json.dump(commande_data, f, indent=4, ensure_ascii=False)

    # Vérifier si tous les plats sont annulés
    annuler_commande(chemin_fichier)

    # Rafraîchir l'affichage
    affichage_commande_actuelle()
