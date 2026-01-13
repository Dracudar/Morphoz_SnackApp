'''
Sauvegarde et chargement des chemins de fichiers et dossiers depuis un fichier de configuration JSON.
Fichier : config.py
'''

import tkinter as tk
import json
import os

# === Variables globales pour les chemins === #
stock_file_path = None  # Variable pour le chemin du fichier de stock
menu_file_path = None  # Variable pour le chemin du fichier de menu
archive_folder_path = None  # Variable pour le chemin du dossier d'archivage

# === Chemin absolu pour 'config.json' === #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Répertoire du fichier
CONFIG_FILE = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'config.json')) # Chemin vers le fichier de configuration

# === Récupération des valeurs des variables de config.json === #
def get_stock_file_path():
    """Retourne la variable stock_file_path."""
    return stock_file_path

def get_menu_file_path():
    """Retourne la variable menu_file_path."""
    return menu_file_path

def get_archive_folder_path():
    """Retourne la variable archive_folder_path."""
    return archive_folder_path

# === Fonctions de chargement des chemins depuis config.json === #
def charger_chemins(): # Charge les chemins des fichiers JSON depuis un fichier de configuration
    """Charge les chemins des fichiers JSON depuis un fichier de configuration."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"stock_file": "", "menu_file": "", "archive_folder": ""}  # Valeurs par défaut si le fichier n'existe pas

def initialiser_chemins(master=None): # Initialise les variables globales pour les chemins
    """Initialise les variables globales pour les chemins."""
    global stock_file_path, menu_file_path, archive_folder_path
    chemins = charger_chemins()
    stock_file_path = tk.StringVar(master=master, value=chemins.get("stock_file", ""))  # Initialisation du fichier de stock
    menu_file_path = tk.StringVar(master=master, value=chemins.get("menu_file", ""))  # Initialisation du fichier de menu
    archive_folder_path = tk.StringVar(master=master, value=chemins.get("archive_folder", ""))  # Initialisation du dossier d'archivage

# === Fonctions de sauvegarde des chemins dans config.json === #
def sauvegarder_chemin_stock(stock_path):  # Sauvegarde uniquement le chemin du fichier stock
    """Sauvegarde le chemin du fichier stock dans le fichier de configuration."""
    data = charger_chemins()
    data["stock_file"] = stock_path
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def sauvegarder_chemin_menu(menu_path):  # Sauvegarde uniquement le chemin du fichier menu
    """Sauvegarde le chemin du fichier menu dans le fichier de configuration."""
    data = charger_chemins()
    data["menu_file"] = menu_path
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def sauvegarder_chemin_dossier(dossier_path):
    """Sauvegarde le chemin du dossier dans le fichier de configuration."""
    data = charger_chemins()
    data["archive_folder"] = dossier_path
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def sauvegarder_chemins(stock_path, menu_path, dossier_path):  # Regroupe les trois sauvegardes
    """Sauvegarde les chemins des fichiers stock, menu et dossier dans le fichier de configuration."""
    sauvegarder_chemin_stock(stock_path)  # Sauvegarde le chemin du fichier stock
    sauvegarder_chemin_menu(menu_path)  # Sauvegarde le chemin du fichier menu
    sauvegarder_chemin_dossier(dossier_path)  # Sauvegarde le chemin du dossier d'archivage

save_chemins = {
    "stock": sauvegarder_chemin_stock,
    "menu": sauvegarder_chemin_menu,
    "dossier": sauvegarder_chemin_dossier,
    "all": sauvegarder_chemins
    }