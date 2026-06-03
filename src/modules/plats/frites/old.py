#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
old.py

Description:
    Interface tkinter temporaire pour l'ajout d'une portion de frites à la commande (version legacy).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.30

Date de modification:
    2026.05.30
"""

# === Importer les modules nécessaires === #
import os  # Pour manipuler les chemins de fichiers

from modules.commandes_saisie.backend.saver import MAJ_commande
from src.backend.chemins_exploitation import (
    charger_donnees_menu, 
    charger_donnees_stock,
    )

# === Définitions des fonctions === #
def add_frites(context):
    """
    Interface pour personnaliser une portion de frites.
    """
    # Charger le prix des frites depuis le fichier menu via context
    menu_data = charger_donnees_menu(context.paths)
    prix_frites = menu_data.get("Frites", {}).get("Prix", 0)

    # Préparer les données du plat
    plat = {
        "Plat": "Frites",
        "Nom": "Portion de frites",
        "Statut": "En attente",
        "Prix": prix_frites,
        "Composition": ["Frites"]
    }

    # Utiliser les chemins d'archive depuis context
    commandes_path = os.path.join(context.paths["archive"], "commandes")
    logs_path = os.path.join(context.paths["archive"], "logs")

    # Ajouter ou mettre à jour la commande
    MAJ_commande(commandes_path, logs_path, plat)
