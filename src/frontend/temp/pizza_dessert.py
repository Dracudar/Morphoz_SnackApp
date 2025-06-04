'''
Code UI pour ajouter une pizza dessert du chef à la commande.
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
def add_dessert(context):
    """
    Interface pour personnaliser une pizza dessert.
    """
    # Charger le prix de la pizza dessert depuis le fichier menu via context
    menu_data = charger_donnees_menu(context.paths)
    prix = menu_data.get("Pizza dessert", {}).get("Prix", 0)

    # Préparer les données du plat
    plat = {
        "Plat": "Pizza dessert",
        "Nom": "Pizza Choco-Banane",
        "Statut": "En attente",
        "Prix": prix,
        "Composition": ["Banane", "Nutella"]
    }

    # Utiliser les chemins d'archive depuis context
    commandes_path = os.path.join(context.paths["archive"], "commandes")
    logs_path = os.path.join(context.paths["archive"], "logs")

    # Ajouter ou mettre à jour la commande
    MAJ_commande(commandes_path, logs_path, plat)

    # Rafraîchir l'affichage de la commande actuelle
    from ..commandes_saisie import affichage_commande_actuelle
    affichage_commande_actuelle(context)
