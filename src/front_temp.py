"""
Code UI pour les interfaces temporaire de l'application SnackApp :
- Personnalisation des pizzas
- Personnalisation des grillades
- Personnalisation des salades composées
- Gestion des stocks
"""

# === Importer les modules nécessaires === #
# == Fonctions utilitaires et de configuration == #
from src.utils import charger_donnees_menu, get_menu_file_path 

# == Modules graphiques == #
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# === Interface "travaux en cours" === #
def travaux_en_cours(root):
    """
    Fenêtre pour indiquer que la fonctionnalité est en cours de développement.
    """
    messagebox.showinfo(
        "Travaux en cours",
        "Cette fonctionnalité est en cours de développement."
    )

# === Personnalisation des plats === #
# == Interface pizza == #
def perso_pizza(root):
    pizza_interface_recette(root)

def pizza_interface_recette(root):
    """
    Fenêtre pour sélectionner une recette de pizza.
    """
    # Charger les données du menu
    menu_data = charger_donnees_menu(get_menu_file_path().get())
    recettes_pizza = menu_data.get("Pizza", {}).get("Recettes", {})

    # Crée une fenêtre pour la sélection des recettes
    fenetre_pizza_1 = tk.Toplevel(root)
    fenetre_pizza_1.title("Pizza - Choix de la Recette")
    fenetre_pizza_1.configure(bg="#2b2b2b")

    # Vérifier si des recettes sont disponibles
    if not recettes_pizza:
        ttk.Label(
            fenetre_pizza_1,
            text="Aucune recette de pizza disponible.",
            background="#2b2b2b",
            foreground="white"
        ).pack(padx=10, pady=10)
        return

    # Ajouter les boutons pour chaque recette
    ttk.Label(
        fenetre_pizza_1,
        text="Choisissez une recette :",
        font=("Cambria", 14),
        background="#2b2b2b",
        foreground="white"
    ).pack(pady=10)

    for nom_recette, details_recette in recettes_pizza.items():
        ttk.Button(
            fenetre_pizza_1,
            text=nom_recette,
            command=lambda r=details_recette: pizza_interface_personnalisation(root, fenetre_pizza_1, r, menu_data)
        ).pack(fill="x", padx=20, pady=5)
    
    # Ajuster automatiquement la taille de la fenêtre
    fenetre_pizza_1.update_idletasks()  # Recalcule la taille en fonction des widgets
    fenetre_pizza_1.geometry("")  # Ajuste automatiquement la taille

def pizza_interface_personnalisation(root, fenetre_pizza_1, recette, menu_data):
    """
    Fenêtre de personnalisation des ingrédients après avoir sélectionné une recette.
    """
    # Fermer la première fenêtre
    fenetre_pizza_1.destroy()

    # Crée une fenêtre pour la personnalisation
    fenetre_pizza_2 = tk.Toplevel(root)
    fenetre_pizza_2.title("Pizza - Personnalisation")
    fenetre_pizza_2.configure(bg="#2b2b2b")

    # Bases disponibles
    bases_disponibles = menu_data.get("Pizza", {}).get("Base", [])
    base_selectionnee = tk.StringVar(value=recette.get("Base", [])[0] if recette.get("Base") else "")

    # Ingrédients disponibles
    ingredients_disponibles = menu_data.get("Pizza", {}).get("Ingrédients", [])
    ingredients_selectionnes = {ingredient: tk.BooleanVar(value=(ingredient in recette.get("Ingrédients", [])))
                                 for ingredient in ingredients_disponibles}

    # Créer un frame principal pour organiser les colonnes
    main_frame = ttk.Frame(fenetre_pizza_2)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Colonne pour les bases
    ttk.Label(
        main_frame,
        text="Base :",
        font=("Cambria", 12),
        background="#2b2b2b",
        foreground="white"
    ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

    base_frame = ttk.Frame(main_frame)
    base_frame.grid(row=1, column=0, padx=10, pady=10, sticky="n")

    for i, base in enumerate(bases_disponibles):
        ttk.Radiobutton(
            base_frame,
            text=base,
            variable=base_selectionnee,
            value=base,
            style="TRadiobutton",
            width=20  # Uniformiser la largeur
        ).grid(row=i, column=0, padx=5, pady=5, sticky="w")  # Une seule colonne pour les bases

    # Colonne pour les ingrédients
    ttk.Label(
        main_frame,
        text="Ingrédients :",
        font=("Cambria", 12),
        background="#2b2b2b",
        foreground="white"
    ).grid(row=0, column=1, padx=10, pady=10, sticky="w")

    ingredients_frame = ttk.Frame(main_frame)
    ingredients_frame.grid(row=1, column=1, padx=10, pady=10, sticky="n")

    for i, (ingredient, var) in enumerate(ingredients_selectionnes.items()):
        ttk.Checkbutton(
            ingredients_frame,
            text=ingredient,
            variable=var,
            style="TCheckbutton",
            width=20  # Uniformiser la largeur
        ).grid(row=i, column=0, padx=5, pady=5, sticky="w")  # Une seule colonne pour les ingrédients

    # Bouton pour valider la personnalisation
    ttk.Button(
        fenetre_pizza_2,
        text="Valider",
        command=lambda: pizza_validation(base_selectionnee, ingredients_selectionnes, fenetre_pizza_2)
    ).pack(pady=20)

    # Ajuster automatiquement la taille de la fenêtre
    fenetre_pizza_2.update_idletasks()  # Recalcule la taille en fonction des widgets
    fenetre_pizza_2.geometry("")  # Ajuste automatiquement la taille

# Validation de la personnalisation
def pizza_validation(base_selectionnee, ingredients_selectionnes, fenetre_pizza_2):
    """
    Valide la personnalisation de la pizza et affiche les choix sélectionnés.
    """
    base = base_selectionnee.get()
    ingredients = [ingredient for ingredient, var in ingredients_selectionnes.items() if var.get()]

    # Afficher les choix dans la console (ou les sauvegarder pour une commande)
    print(f"Base sélectionnée : {base}")
    print(f"Ingrédients sélectionnés : {', '.join(ingredients)}")

    # Fermer la fenêtre de personnalisation
    fenetre_pizza_2.destroy()

# == Interface grillade == #
def perso_grillade(root):
    travaux_en_cours(root)

# == Interface salades composées == #
def perso_salade_composee(root):
    travaux_en_cours(root)

# == Interface salades composées == #
def perso_frites(root):
    travaux_en_cours(root)

# == Interface gestion des stocks == #
def gestion_stock(root):
    travaux_en_cours(root)