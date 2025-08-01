'''

'''

import os
import json
from datetime import datetime
from .commandes_utils import charger_fichier_commande
from .printer import print_ticket_recap, print_ticket_cuisine

def valider_commande(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        return

    # TODO : mettre en place le système de paiement (CB, espèces, repas gratuits) et mettre à jour le type de paiement dans le fichier JSON
    
    # Mettre à jour la date de validation
    commande["Informations"]["Date de validation"] = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]

    # Impression des tickets pour chaque plat mis en préparation
    print_ticket_recap(chemin_fichier)
    print_ticket_cuisine(chemin_fichier)

    # Mettre à jour les statuts
    commande["Informations"]["Statut"] = "Validée"
    for plat in commande["Commande"].values():
        if plat["Statut"] == "En attente":
            plat["Statut"] = "En préparation"

    # TODO : Mettre en place un système d'impression de ticket de commande
    # 1 ticket par plat mis en préparation avec l'ID complet, le nom du plat et la composition
    # 1 ticket récapitulatif avec l'ID de la commande, le montant total, le type de paiement et la date de validation, la liste des plats mis en préparation (numéro de plat et nom du plat)

    # Sauvegarder les modifications de la commande
    with open(chemin_fichier, "w", encoding="utf-8") as fichier:
        json.dump(commande, fichier, indent=4, ensure_ascii=False)

    # Sauvegarder le stock modifié
    if hasattr(context, "stock_cache"):
        context.stock_cache.save()

    # Déplacer le fichier
    dossier_en_cours = os.path.join(os.path.dirname(chemin_fichier), "en_cours")
    os.makedirs(dossier_en_cours, exist_ok=True)
    os.rename(chemin_fichier, os.path.join(dossier_en_cours, os.path.basename(chemin_fichier)))

    # Rafraîchir l'affichage
    affichage_commande_actuelle(context)
    affichage_commandes_validées(context)

# == Annulation de commande == #
def annuler_commande(chemin_fichier):
    commande = charger_fichier_commande(chemin_fichier)
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

def annuler_plat(context, chemin_fichier, plat_id, affichage_commande_actuelle):
    """
    Annule un plat dans la commande en cours.
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return

    # Mettre à jour le statut du plat
    commande_data["Commande"][plat_id]["Statut"] = "Annulé"

    # Récupérer le plat annulé
    plat_annule = commande_data["Commande"][plat_id]
    # Ré-incrémenter le stock selon le type de plat
    if hasattr(context, "stock_cache"):
        refresh_needed = False
        # Pizza ou pizza dessert
        if plat_annule["Plat"] == "Pizza" or plat_annule["Plat"] == "Pizza dessert":
            was_out = context.stock_cache.is_out_of_stock(["Plats", "Pizza", "Pâte à pizza"])
            context.stock_cache.incrementer(["Plats", "Pizza", "Pâte à pizza"])
            is_out = context.stock_cache.is_out_of_stock(["Plats", "Pizza", "Pâte à pizza"])
            if was_out != is_out:
                refresh_needed = True
        # Grillade
        elif plat_annule["Plat"] == "Grillade":
            viandes = plat_annule["Composition"]["Viandes"]
            was = {v: context.stock_cache.is_out_of_stock(["Plats", "Grillades", v]) for v in viandes}
            for viande, quantite in viandes.items():
                context.stock_cache.incrementer(["Plats", "Grillades", viande], n=quantite)
            changed = any(was[v] != context.stock_cache.is_out_of_stock(["Plats", "Grillades", v]) for v in viandes)
            if changed:
                refresh_needed = True
        # Frites
        elif plat_annule["Plat"] == "Frites":
            was_out = context.stock_cache.is_out_of_stock(["Accompagnement", "Frites"])
            context.stock_cache.incrementer(["Accompagnement", "Frites"])
            is_out = context.stock_cache.is_out_of_stock(["Accompagnement", "Frites"])
            if was_out != is_out:
                refresh_needed = True
        # Salade composée
        elif plat_annule["Plat"] == "Salade composée":
            was_out = context.stock_cache.is_out_of_stock(["Plats", "Salade composée"])
            context.stock_cache.incrementer(["Plats", "Salade composée"])
            is_out = context.stock_cache.is_out_of_stock(["Plats", "Salade composée"])
            if was_out != is_out:
                refresh_needed = True

        if refresh_needed:
            from ..frontend.boutons_menu import affichage_menu
            affichage_menu(context, context.images_references if hasattr(context, "images_references") else [])

    # Recalculer le montant total
    commande_data["Informations"]["Montant"] = sum(
        plat["Prix"] for plat in commande_data["Commande"].values() if plat["Statut"] != "Annulé"
    )
    
    # Sauvegarder les modifications
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande_data, f, indent=4, ensure_ascii=False)

    # Vérifier si tous les plats sont annulés
    annuler_commande(chemin_fichier)

    # Rafraîchir l'affichage
    affichage_commande_actuelle(context)

def annuler_all_plats(context, chemin_fichier, affichage_commande_actuelle):
    """
    Annule tous les plats dans la commande en cours.
    """
    commande_data = charger_fichier_commande(chemin_fichier)
    if not commande_data:
        return
    # Mettre à jour le statut de tous les plats
    for plat_id, plat in commande_data["Commande"].items():
        if plat["Statut"] == "En attente":
            annuler_plat(context, chemin_fichier, plat_id, affichage_commande_actuelle)
