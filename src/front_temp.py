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
    fenetre_pizza_1.attributes("-topmost", True)  # Garde la fenêtre au premier plan

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
    fenetre_pizza_2.attributes("-topmost", True)  # Garde la fenêtre au premier plan

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
    """
    Interface pour personnaliser une grillade.
    """
    # Charger les données du menu
    menu_data = charger_donnees_menu(get_menu_file_path().get())
    grillade_data = menu_data.get("Grillade", {})
    viandes_disponibles = grillade_data.get("Viande(s)", {})
    accompagnements_disponibles = grillade_data.get("Accompagnement", [])

    # Crée une fenêtre pour la personnalisation
    fenetre_grillade = tk.Toplevel(root)
    fenetre_grillade.title("Grillade - Personnalisation")
    fenetre_grillade.configure(bg="#2b2b2b")
    fenetre_grillade.attributes("-topmost", True)  # Garde la fenêtre au premier plan

    # Variables pour suivre les quantités de viandes
    quantites_viandes = {viande: tk.IntVar(value=0) for viande in viandes_disponibles}

    # Variable pour l'accompagnement sélectionné
    accompagnement_selectionne = tk.StringVar(value=accompagnements_disponibles[0] if accompagnements_disponibles else "")

    # Fonction pour mettre à jour les quantités
    def ajuster_quantite(viande, delta):
        """
        Ajuste la quantité de viande sélectionnée en respectant la limite totale de 2 portions.
        """
        # Récupère la valeur de la viande depuis le dictionnaire
        valeur_viande = viandes_disponibles.get(viande, 0)
        
        # Calcule le total actuel en fonction des quantités et des valeurs des viandes
        total_actuel = sum(quantites_viandes[v].get() * viandes_disponibles.get(v, 0) for v in quantites_viandes)

        # Calcule la nouvelle valeur
        nouvelle_valeur = quantites_viandes[viande].get() + delta

        # Vérifie que le total ne dépasse pas 2 portions
        if 0 <= nouvelle_valeur * valeur_viande + total_actuel - quantites_viandes[viande].get() * valeur_viande <= 2:
            quantites_viandes[viande].set(nouvelle_valeur)

    # Affichage des viandes
    ttk.Label(
        fenetre_grillade,
        text="Choisissez vos viandes (max 2 portions) :",
        font=("Cambria", 14),
        background="#2b2b2b",
        foreground="white"
    ).pack(pady=10)

    for viande in viandes_disponibles:
        frame_viande = ttk.Frame(fenetre_grillade)
        frame_viande.pack(fill="x", padx=20, pady=5)

        ttk.Label(
            frame_viande,
            text=viande,
            font=("Cambria", 12),
            width=20
        ).pack(side="left")

        ttk.Button(
            frame_viande,
            text="-",
            command=lambda v=viande: ajuster_quantite(v, -1)
        ).pack(side="left", padx=5)

        ttk.Label(
            frame_viande,
            textvariable=quantites_viandes[viande],
            width=5,
            anchor="center"
        ).pack(side="left")

        ttk.Button(
            frame_viande,
            text="+",
            command=lambda v=viande: ajuster_quantite(v, 1)
        ).pack(side="left", padx=5)

    # Affichage des accompagnements
    ttk.Label(
        fenetre_grillade,
        text="Choisissez un accompagnement :",
        font=("Cambria", 14),
        background="#2b2b2b",
        foreground="white"
    ).pack(pady=10)

    frame_accompagnements = ttk.Frame(fenetre_grillade)
    frame_accompagnements.pack(pady=10)

    for i, accompagnement in enumerate(accompagnements_disponibles):
        ttk.Radiobutton(
            frame_accompagnements,
            text=accompagnement,
            variable=accompagnement_selectionne,
            value=accompagnement,
            style="TRadiobutton",
            width=20  # Uniformiser la largeur
        ).grid(row=0, column=i, padx=5, pady=5, sticky="w")  # Positionner côte à côte

    # Bouton pour valider la personnalisation
    def valider_grillade():
        viandes_choisies = {viande: quantites_viandes[viande].get() for viande in viandes_disponibles if quantites_viandes[viande].get() > 0}
        accompagnement = accompagnement_selectionne.get()

        # Afficher les choix dans la console (ou les sauvegarder pour une commande)
        print(f"Viandes choisies : {viandes_choisies}")
        print(f"Accompagnement choisi : {accompagnement}")

        # Fermer la fenêtre
        fenetre_grillade.destroy()

    ttk.Button(
        fenetre_grillade,
        text="Valider",
        command=valider_grillade
    ).pack(pady=20)

    # Ajuster automatiquement la taille de la fenêtre
    fenetre_grillade.update_idletasks()
    fenetre_grillade.geometry("")

# == Interface salades composées == #
def perso_salade_composee(root):
    travaux_en_cours(root)

# == Interface salades composées == #
def perso_frites(root):
    travaux_en_cours(root)

# == Interface gestion des stocks == #
def gestion_stock(root):
    travaux_en_cours(root)