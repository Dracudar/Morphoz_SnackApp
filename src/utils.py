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
stock_file_path = None  # Variable pour le chemin du fichier de stock
menu_file_path = None  # Variable pour le chemin du fichier de menu
archive_folder_path = None  # Variable pour le chemin du dossier d'archivage

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

# === Recherche de fichiers et dossiers === #
def chercher_fichier(): # Ouvre un explorateur de fichiers pour sélectionner un fichier JSON
    '''Ouvre un explorateur de fichiers pour sélectionner un fichier JSON.'''
    filepath = filedialog.askopenfilename(
        filetypes=[("Fichiers JSON", "*.json")],
        title="Sélectionner un fichier JSON"
    )
    return filepath

def chercher_dossier():  # Ouvre un explorateur de fichiers pour sélectionner un dossier
    """Ouvre un explorateur de fichiers pour sélectionner un dossier."""
    folder_path = filedialog.askdirectory(
        title="Sélectionner un dossier pour l'archivage et le suivi"
    )
    return folder_path

# === Chargement et sauvegarde des chemins === #
def charger_chemins(): # Charge les chemins des fichiers JSON depuis un fichier de configuration
    """Charge les chemins des fichiers JSON depuis un fichier de configuration."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"stock_file": "", "menu_file": "", "archive_folder": ""}  # Valeurs par défaut si le fichier n'existe pas

def initialiser_chemins(): # Initialise les variables globales pour les chemins
    """Initialise les variables globales pour les chemins."""
    global stock_file_path, menu_file_path, archive_folder_path
    chemins = charger_chemins()
    stock_file_path = tk.StringVar(value=chemins.get("stock_file", ""))  # Initialisation du fichier de stock
    menu_file_path = tk.StringVar(value=chemins.get("menu_file", ""))  # Initialisation du fichier de menu
    archive_folder_path = tk.StringVar(value=chemins.get("archive_folder", ""))  # Initialisation du dossier d'archivage

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

# === Dossier d'archivage === #
def initialiser_dossier_archive():
    """Initialise le dossier d'archivage et crée la structure si nécessaire."""
    chemins = charger_chemins()
    dossier_path = chemins.get("archive_folder", "")

    if dossier_path:
        # Créer la structure de dossiers si elle n'existe pas
        logs_path = os.path.join(dossier_path, "logs") # Définie le dossier des logs
        os.makedirs(logs_path, exist_ok=True) # Crée le dossier des logs

        commandes_path = os.path.join(dossier_path, "commandes") # Définie le dossier des commandes
        os.makedirs(commandes_path, exist_ok=True) # Crée le dossier des commandes

        en_cours_path = os.path.join(commandes_path, "en_cours") # Définie le dossier des commandes en cours
        os.makedirs(en_cours_path, exist_ok=True) # Crée le dossier des commandes en cours

        terminee_path = os.path.join(commandes_path, "terminee") # Définie le dossier des commandes terminées
        os.makedirs(terminee_path, exist_ok=True) # Crée le dossier des commandes terminées

        annulee_path = os.path.join(commandes_path, "annulee") # Définie le dossier des commandes annulées
        os.makedirs(annulee_path, exist_ok=True) # Crée le dossier des commandes annulées

        corrompu_path = os.path.join(commandes_path, "corrompu") # Définie le dossier des fichiers de commandes corrompus
        os.makedirs(corrompu_path, exist_ok=True) # Crée le dossier des fichiers de commandes corrompus
        
    else:
        raise ValueError("Le chemin du dossier d'archivage n'est pas défini dans le fichier de configuration.")

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