#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paiements.py

Description:
    Mise à jour du mode de paiement dans le fichier de commande et déclenchement de la validation avec impression des tickets.

Author :
    Dracudar

Version:
    1.2

Date de création :
    2025.06.07

Date de modification:
    2026.06.19
"""

from src.backend.commandes_utils import acceder_commande
from src.modules.commandes_saisie.backend.gestion import valider_commande


def paiement_carte(chemin_fichier):
    """Enregistre le paiement par carte dans la commande et déclenche la validation."""
    with acceder_commande(chemin_fichier) as commande:
        if not commande:
            return
        commande["Informations"]["Type de paiement"] = "Carte"
    valider_commande(chemin_fichier)

def paiement_especes(chemin_fichier):
    """Enregistre le paiement en espèces dans la commande et déclenche la validation."""
    with acceder_commande(chemin_fichier) as commande:
        if not commande:
            return
        commande["Informations"]["Type de paiement"] = "Espèces"
    valider_commande(chemin_fichier)

def gratuit(chemin_fichier):
    """Enregistre un repas gratuit dans la commande et déclenche la validation."""
    with acceder_commande(chemin_fichier) as commande:
        if not commande:
            return
        commande["Informations"]["Type de paiement"] = "Repas gratuit"
    valider_commande(chemin_fichier)
