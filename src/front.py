'''
Module des fonctions graphiques de base de l'application SnackApp Morphoz
'''

# == Modules graphiques == #
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
root = tk.Tk()

# === Fonctions générales === #
def back_frame(): # Fonction pour créer le cadre principal de l'application
    """ Cette section crée la fenêtre principale de l'application, configure son apparence et mappe des touches pour la gestion du plein écran. """
    # == Configuration de la fenêtre principale == #
    global root
    root.title("SnackApp Morphoz")  # Titre de la fenêtre
    # root.iconbitmap("assets/logo.ico")  # Icône de la fenêtre -> à créer
    root.geometry("800x600")  # Taille de la fenêtre
    root.attributes('-fullscreen', True)  # Active le mode plein écran
    root.configure(bg="#2b2b2b")  # Couleur de fond sombre

    # == Mappage des touches == #
    root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False)) # Quitter le mode plein écran avec Échap
    root.bind("<F11>", lambda event: root.attributes('-fullscreen', True)) # Passer en plein écran avec F11
    root.bind("<Control-q>", lambda event: quitter_app())  # Quitter l'application avec Ctrl+Q

def quitter_app():
    """Fonction pour quitter l'application."""
    root.destroy()  # Fermer la fenêtre

# === Export === #
__all__ = ["tk", "ttk", "messagebox", "root"]  # Liste des noms de modules graphiques à exporter
base_frame = {
    "back": back_frame,
    "quitter": quitter_app
    }