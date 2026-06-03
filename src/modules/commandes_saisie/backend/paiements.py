#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paiements.py

Description:
    Mise à jour du mode de paiement dans le fichier de commande et déclenchement de la validation avec impression des tickets.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2025.06.07

Date de modification:
    2026.05.30
"""

import json  # Pour manipuler les données JSON
from ....backend.commandes_utils import charger_fichier_commande  # Pour charger le fichier de commande JSON
from .gestion import valider_commande  # Pour valider la commande après paiement et imprimer les tickets

    
def paiement_carte(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
        commande = charger_fichier_commande(chemin_fichier)
        commande["Informations"]["Type de paiement"] = "Carte"  # Met à jour le type de paiement dans la commande
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande, f, indent=4, ensure_ascii=False)

        valider_commande(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées)

def paiement_especes(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
        commande = charger_fichier_commande(chemin_fichier)
        commande["Informations"]["Type de paiement"] = "Espèces"  # Met à jour le type de paiement dans la commande
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande, f, indent=4, ensure_ascii=False)

        valider_commande(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées)


def gratuit(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
    commande = charger_fichier_commande(chemin_fichier)
    commande["Informations"]["Type de paiement"] = "Repas gratuit"  # Met à jour le type de paiement dans la commande
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande, f, indent=4, ensure_ascii=False)

    valider_commande(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées)