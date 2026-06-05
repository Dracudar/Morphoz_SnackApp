#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paiements.py

Description:
    Mise à jour du mode de paiement dans le fichier de commande et déclenchement de la validation avec impression des tickets.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2025.06.07

Date de modification:
    2026.06.04
"""

import json
from src.backend.commandes_utils import charger_fichier_commande
from src.modules.commandes_saisie.backend.gestion import valider_commande


def paiement_carte(chemin_fichier):
    """Enregistre le paiement par carte dans la commande et déclenche la validation."""
    commande = charger_fichier_commande(chemin_fichier)
    # Mettre à jour le type de paiement dans la commande
    commande["Informations"]["Type de paiement"] = "Carte"
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande, f, indent=4, ensure_ascii=False)
    valider_commande(chemin_fichier)

def paiement_especes(chemin_fichier):
    """Enregistre le paiement en espèces dans la commande et déclenche la validation."""
    commande = charger_fichier_commande(chemin_fichier)
    # Mettre à jour le type de paiement dans la commande
    commande["Informations"]["Type de paiement"] = "Espèces"
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande, f, indent=4, ensure_ascii=False)
    valider_commande(chemin_fichier)

def gratuit(chemin_fichier):
    """Enregistre un repas gratuit dans la commande et déclenche la validation."""
    commande = charger_fichier_commande(chemin_fichier)
    # Mettre à jour le type de paiement dans la commande
    commande["Informations"]["Type de paiement"] = "Repas gratuit"
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande, f, indent=4, ensure_ascii=False)
    valider_commande(chemin_fichier)
