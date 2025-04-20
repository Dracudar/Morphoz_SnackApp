# === Importer les modules nécessaires === #
# == Fonctions utilitaires et de configuration == #
from src.utils import charger_donnees_menu, get_menu_file_path 

# == Modules graphiques == #
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# === Personnalisation des plats === #
# == Interface pizza == #
def interface_pizza_1(frame_temp_pizza_1):
    """
    Gère l'interface de personnalisation des pizzas dans le cadre temporaire.
    """
    # Charger les données du menu
    menu_data = charger_donnees_menu(get_menu_file_path().get())

    # Supprimer tous les widgets existants dans le cadre temporaire
    for widget in frame_temp_pizza_1.winfo_children():
        widget.destroy()

    # Récupérer les recettes de pizza
    recettes_pizza = menu_data.get("Pizza", {}).get("Recettes", {})

    # Vérifier si des recettes sont disponibles
    if not recettes_pizza:
        ttk.Label(
            frame_temp_pizza_1,
            text="Aucune recette de pizza disponible.",
            style="TLabel",
            background="#2b2b2b",
            foreground="white"
        ).pack(padx=10, pady=10)
        return

    # Ajouter les boutons pour chaque recette
    row = 0
    col = 0
    for nom_recette, details_recette in recettes_pizza.items():
        if nom_recette == "Personnalisable":
            ttk.Button(
                frame_temp_pizza_1,
                text=nom_recette,
                command=lambda r=details_recette: selectionner_pizza(r)
            ).grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
            row += 1
            continue

        ttk.Button(
            frame_temp_pizza_1,
            text=nom_recette,
            command=lambda r=details_recette: selectionner_pizza(r)
        ).grid(row=row, column=col, padx=10, pady=5, sticky="ew")

        col += 1
        if col > 1:
            col = 0
            row += 1

# Fonction pour gérer la sélection d'une pizza
def selectionner_pizza(recette):
    details = recette.get('details', 'Aucun détail disponible.')
    messagebox.showinfo("Sélection", f"Vous avez sélectionné : {recette.get('nom', 'Pizza inconnue')}\nDétails : {details}")
