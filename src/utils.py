'''
Sous-fichier comprenant diverses fonctions utilitaires pour le projet SnackApp.
'''
# === Importer les modules nécessaires === #
# == Fonctions utilitaires et de configuration == #
import json
import os
from PIL import Image, ImageTk

# == Modules graphiques == #
import tkinter as tk
from tkinter import filedialog

# Définir le chemin absolu pour config.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Répertoire du fichier utils.py
CONFIG_FILE = os.path.join(BASE_DIR, "../assets/config.json") # Chemin vers le fichier de configuration

# Variables globales pour les chemins
stock_file_path = None
menu_file_path = None

# === Récupération des valeurs des variables de config.json === #
def get_stock_file_path():
    """Retourne la variable stock_file_path."""
    return stock_file_path

def get_menu_file_path():
    """Retourne la variable menu_file_path."""
    return menu_file_path

# === Choix des fichiers JSON === #
def chercher_fichier(): # Ouvre un explorateur de fichiers pour sélectionner un fichier JSON
    '''Ouvre un explorateur de fichiers pour sélectionner un fichier JSON.'''
    filepath = filedialog.askopenfilename(
        filetypes=[("Fichiers JSON", "*.json")],
        title="Sélectionner un fichier JSON"
    )
    return filepath

def charger_chemins(): # Charge les chemins des fichiers JSON depuis un fichier de configuration
    """Charge les chemins des fichiers JSON depuis un fichier de configuration."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"stock_file": "", "menu_file": ""}

def initialiser_chemins(): # Initialise les variables globales pour les chemins
    """Initialise les variables globales pour les chemins."""
    global stock_file_path, menu_file_path
    chemins = charger_chemins()
    stock_file_path = tk.StringVar(value=chemins.get("stock_file", ""))
    menu_file_path = tk.StringVar(value=chemins.get("menu_file", ""))

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

def sauvegarder_chemins(stock_path, menu_path):  # Regroupe les deux sauvegardes
    """Sauvegarde les chemins des fichiers stock et menu dans le fichier de configuration."""
    sauvegarder_chemin_stock(stock_path)
    sauvegarder_chemin_menu(menu_path)

# === Chargement des données JSON === #
def charger_donnees_stock(stock_file_path):
    """
    Charge les données du fichier JSON de stock.

    :param stock_file_path: Chemin vers le fichier JSON de stock.
    :return: Données du fichier sous forme de dictionnaire.
    """
    try:
        with open(stock_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier de stock '{stock_file_path}' est introuvable.")
    except json.JSONDecodeError:
        raise ValueError(f"Le fichier de stock '{stock_file_path}' contient des données invalides.")

def charger_donnees_menu(menu_file_path):
    """
    Charge les données du fichier JSON de menu.

    :param menu_file_path: Chemin vers le fichier JSON de menu.
    :return: Données du fichier sous forme de dictionnaire.
    """
    try:
        with open(menu_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier de menu '{menu_file_path}' est introuvable.")
    except json.JSONDecodeError:
        raise ValueError(f"Le fichier de menu '{menu_file_path}' contient des données invalides.")

# === Chargement et redimensionnement d'images === #
def charger_img(nom_image, taille=()):
    """
    Charge et redimensionne une image pour tkinter depuis le dossier assets/img.

    :param nom_image: Nom du fichier image (ex. "image.png").
    :param taille: Tuple (largeur, hauteur) pour redimensionner l'image.
    :return: ImageTk.PhotoImage pour utilisation dans tkinter.
    """
    chemin = os.path.join(os.path.dirname(__file__), "../assets/img", nom_image)
    try:
        img = Image.open(chemin)
        img = img.resize(taille, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except FileNotFoundError:
        raise FileNotFoundError(f"L'image '{nom_image}' est introuvable dans 'assets/img'.")
    except Exception as e:
        raise RuntimeError(f"Une erreur est survenue lors du chargement de l'image '{nom_image}': {e}")
