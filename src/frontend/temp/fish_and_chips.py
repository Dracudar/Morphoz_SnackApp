'''
Code UI pour ajouter un Fish & Chips à la commande.
'''

# === Importer les modules nécessaires === #
import os  # Pour manipuler les chemins de fichiers
import tkinter as tk
from tkinter import ttk, messagebox

from src.backend.commandes_saisie_save import MAJ_commande
from src.frontend.temp_gestion import ouvrir_fenetre_unique 
from ...backend.chemins_exploitation import (
    charger_donnees_menu, 
    charger_donnees_stock,
    )

# === Définitions des fonctions === #
def add_fish_and_chips(context):
    """
    Interface pour personnaliser une portion de Fish & Chips.
    """
    # Charger le prix des Fish & Chips depuis le fichier menu via context
    menu_data = charger_donnees_menu(context.paths)
    prix = menu_data.get("Fish & Chips", {}).get("Prix", 0)

    # Préparer les données du plat
    plat = {
        "Plat": "Fish & Chips",
        "Nom": "Portion de Fish & Chips",
        "Statut": "En attente",
        "Prix": prix,
        "Composition": "Poisson panné + Frites"
    }

    # Utiliser les chemins d'archive depuis context
    commandes_path = os.path.join(context.paths["archive"], "commandes")
    logs_path = os.path.join(context.paths["archive"], "logs")

    # Ajouter ou mettre à jour la commande
    MAJ_commande(commandes_path, logs_path, plat)

    # Rafraîchir l'affichage de la commande actuelle
    from ..commandes_saisie import affichage_commande_actuelle
    affichage_commande_actuelle(context)
