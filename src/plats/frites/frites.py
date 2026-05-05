'''
Code UI pour ajouter une portion de frites à la commande
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

    # Rafraîchir l'affichage de la commande actuelle
    from ...frontend.commandes_saisie import affichage_commande_actuelle
    affichage_commande_actuelle(context)
