'''
Code UI pour les interfaces temporaire personnalisation des portions de frites
'''

# === Importer les modules nécessaires === #
from src.utils import (
    charger_donnees_menu, 
    charger_donnees_stock,
    )
from src.utils import (
    get_menu_file_path,
    get_stock_file_path,
    get_archive_folder_path
    )
from src.back import ajouter_ou_mettre_a_jour_commande
import os  # Pour manipuler les chemins de fichiers

# == Modules graphiques == #
from UI.front import * # Modules Tinker
from src.front_temp import * # Modules de gestion des fenêtres

def perso_frites(root):
    travaux_en_cours(root)