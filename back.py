# === Importer les modules nécessaires === #
# == Modules graphiques == #
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from utils import charger_donnees_menu, get_menu_file_path 

# === Personnalisation des plats === #
# == Interface pizza == #
def interface_pizza_1(frame_gauche_milieu):
    # Charger les données du menu à la demande
    menu_data = charger_donnees_menu(get_menu_file_path().get())

    # Supprimer tous les widgets existants dans le cadre gauche du milieu
    for widget in frame_gauche_milieu.winfo_children():
        widget.destroy()
    
    # Récupérer les recettes de pizza
    recettes_pizza = menu_data.get("Pizza", {}).get("Recettes", {})

    # Vérifier si des recettes sont disponibles
    if not recettes_pizza:
        ttk.Label(
            frame_gauche_milieu,
            text="Aucune recette de pizza disponible.",
            style="TLabel",
            background="#2b2b2b",
            foreground="white"
        ).pack(padx=10, pady=10)
        return

    # Créer un bouton pour chaque recette de pizza
    for nom_recette, details_recette in recettes_pizza.items():
        ttk.Button(
            frame_gauche_milieu,
            text=nom_recette,  # Utiliser le nom de la recette (clé)
            command=lambda r=details_recette: selectionner_pizza(r)  # Associer une commande pour sélectionner la pizza
        ).pack(padx=10, pady=5, fill="x")

# Fonction pour gérer la sélection d'une pizza
def selectionner_pizza(recette):
    messagebox.showinfo("Sélection", f"Vous avez sélectionné : {recette.get('nom', 'Pizza inconnue')}")
