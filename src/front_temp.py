'''
Code UI pour les interfaces temporaire de l'application SnackApp :
- Personnalisation des pizzas
- Personnalisation des grillades
- Personnalisation des salades composées
- Gestion des stocks
'''

# === Importer les modules nécessaires === #
# == Fonctions utilitaires et de configuration == #
from src.utils import (
    charger_donnees_menu, 
    charger_donnees_stock,
    sauvegarder_chemin_stock
    )
from src.utils import (
    get_menu_file_path,
    get_stock_file_path,
    get_archive_folder_path
    )
from src.back import ajouter_ou_mettre_a_jour_commande
from functools import partial
import os  # Pour manipuler les chemins de fichiers

# == Modules graphiques == #
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# === Suivi des fenêtres ouvertes === #
fenetres_ouvertes: dict[str, tk.Toplevel] = {}

def ouvrir_fenetre_unique(titre, creation_fenetre, fermer_autres=False):
    """
    Vérifie si une fenêtre avec le même titre est déjà ouverte.
    Si oui, ramène cette fenêtre au premier plan.
    Sinon, crée une nouvelle fenêtre.
    Si `fermer_autres` est True, ferme les autres fenêtres avant d'ouvrir la nouvelle.
    """
    if fermer_autres:
        # Fermer toutes les fenêtres ouvertes
        for fenetre in list(fenetres_ouvertes.values()):
            if fenetre.winfo_exists():
                fenetre.destroy()
        fenetres_ouvertes.clear()

    if titre in fenetres_ouvertes and fenetres_ouvertes[titre].winfo_exists():
        # Ramène la fenêtre existante au premier plan
        fenetres_ouvertes[titre].lift()
        fenetres_ouvertes[titre].focus_force()
    else:
        # Crée une nouvelle fenêtre et l'ajoute au dictionnaire
        fenetre = creation_fenetre()
        fenetres_ouvertes[titre] = fenetre

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
    def creation_fenetre():
        # Charger les données du menu
        menu_data = charger_donnees_menu(get_menu_file_path().get())
        recettes_pizza = menu_data.get("Pizza", {}).get("Recettes", {})

        # Charger les données du stock
        stock_data = charger_donnees_stock(get_stock_file_path().get())

        # Crée une fenêtre pour la sélection des recettes
        fenetre_pizza_1 = tk.Toplevel(root)
        fenetre_pizza_1.title("Pizza")
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
            return fenetre_pizza_1

        # Ajouter les boutons pour chaque recette
        ttk.Label(
            fenetre_pizza_1,
            text="Choisissez une recette :",
            font=("Cambria", 14),
            background="#2b2b2b",
            foreground="white"
        ).pack(pady=10)

        for nom_recette, details_recette in recettes_pizza.items():
            details_recette["Nom"] = nom_recette  # Ajoutez le nom de la recette au dictionnaire
            ttk.Button(
                fenetre_pizza_1,
                text=nom_recette,
                command=lambda r=details_recette: pizza_interface_personnalisation(root, fenetre_pizza_1, r, stock_data)
            ).pack(fill="x", padx=20, pady=5)

        # Ajuster automatiquement la taille de la fenêtre
        fenetre_pizza_1.update_idletasks()  # Recalcule la taille en fonction des widgets
        fenetre_pizza_1.geometry("")  # Ajuste automatiquement la taille

        return fenetre_pizza_1

    # Utiliser la fonction pour ouvrir une fenêtre unique
    ouvrir_fenetre_unique("Pizza", creation_fenetre, fermer_autres=True)

def pizza_interface_personnalisation(root, fenetre_pizza_1, recette, stock_data):
    """
    Fenêtre de personnalisation des ingrédients après avoir sélectionné une recette.
    """
    # Fermer la première fenêtre
    fenetre_pizza_1.destroy()

    def creation_fenetre():
        # Crée une fenêtre pour la personnalisation
        fenetre_pizza_2 = tk.Toplevel(root)
        fenetre_pizza_2.title("Pizza")
        fenetre_pizza_2.configure(bg="#2b2b2b")
        fenetre_pizza_2.attributes("-topmost", True)  # Garde la fenêtre au premier plan

        # Bases disponibles (sauces)
        bases_disponibles = stock_data.get("Plats", {}).get("Pizza", {}).get("Bases", {})
        bases_disponibles = [base for base, data in bases_disponibles.items() if not data.get("OutOfStock", False)]
        base_selectionnee = tk.StringVar(value=recette.get("Base", [])[0] if recette.get("Base") else "")

        # Ingrédients disponibles (par catégorie)
        ingredients_disponibles = {
            categorie: {
                ingredient: data for ingredient, data in ingredients.items() if not data.get("OutOfStock", False)
            }
            for categorie, ingredients in stock_data.get("Ingrédients", {}).items()
            if categorie != "Pâtes"  # Exclure la catégorie "Pâtes"
        }
        ingredients_selectionnes = {
            ingredient: tk.BooleanVar(value=(ingredient in recette.get("Ingrédients", [])))
            for categorie, ingredients in ingredients_disponibles.items()
            for ingredient in ingredients
        }

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

        row = 0
        for categorie, ingredients in ingredients_disponibles.items():
            # Ajouter un titre pour chaque catégorie
            ttk.Label(
                ingredients_frame,
                text=categorie,
                font=("Cambria", 10, "bold"),
                background="#2b2b2b",
                foreground="white"
            ).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            row += 1

            # Ajouter les ingrédients de la catégorie
            for ingredient in ingredients:
                ttk.Checkbutton(
                    ingredients_frame,
                    text=ingredient,
                    variable=ingredients_selectionnes[ingredient],
                    style="TCheckbutton",
                    width=20
                ).grid(row=row, column=0, padx=5, pady=5, sticky="w")
                row += 1

        # Bouton pour valider la personnalisation
        ttk.Button(
            fenetre_pizza_2,
            text="Valider",
            command=lambda: pizza_validation(base_selectionnee, ingredients_selectionnes, fenetre_pizza_2, recette)
        ).pack(pady=20)

        # Ajuster automatiquement la taille de la fenêtre
        fenetre_pizza_2.update_idletasks()  # Recalcule la taille en fonction des widgets
        fenetre_pizza_2.geometry("")  # Ajuste automatiquement la taille

        return fenetre_pizza_2

    # Utiliser la fonction pour ouvrir une fenêtre unique
    ouvrir_fenetre_unique("Pizza", creation_fenetre, fermer_autres=True)

# Validation de la personnalisation
def pizza_validation(base_selectionnee, ingredients_selectionnes, fenetre_pizza_2, recette=None):
    """
    Valide la personnalisation de la pizza, affiche les choix sélectionnés et ajoute la pizza au fichier de commande.
    """
    base = base_selectionnee.get()
    if not base:
        # Afficher un message d'erreur si aucune base n'est sélectionnée
        messagebox.showerror("Erreur", "Veuillez sélectionner une base pour la pizza.")
        return

    # Ingrédients sélectionnés
    ingredients = [ingredient for ingredient, var in ingredients_selectionnes.items() if var.get()]

    # Calculer les ingrédients retirés et supplémentaires par rapport à la recette
    if recette:
        recette_nom = recette.get("Nom", "personnalisée")  # Utilisez le nom de la recette si disponible
        recette_ingredients = set(recette.get("Ingrédients", []))
        ingredients_non_selectionnes = recette_ingredients - set(ingredients)
        ingredients_supplementaires = set(ingredients) - recette_ingredients
    else:
        recette_nom = "personnalisée"
        recette_ingredients = set()
        ingredients_non_selectionnes = set()
        ingredients_supplementaires = set()

    # Construire le message
    if recette_nom == "Personnalisable":
        message = f"Pizza personnalisée base {base} avec {', '.join(ingredients)}"
    else:
        message = f"Pizza {recette_nom} base {base}"
        if ingredients_non_selectionnes:
            message += f" (sans {', '.join(ingredients_non_selectionnes)})"
        if ingredients_supplementaires:
            message += f" (supplément {', '.join(ingredients_supplementaires)})"

    # Charger le prix des pizzas depuis le fichier menu
    menu_data = charger_donnees_menu(get_menu_file_path().get())
    prix_pizza = menu_data.get("Pizza", {}).get("Prix", 0)

    # Préparer les données du plat
    plat = {
        "Nom": message,  # Utiliser le message comme nom
        "Statut": "En attente",
        "Prix": prix_pizza,  # Utiliser le prix global des pizzas
        "Composition": {
            "Base": base,
            "Ingrédients": ingredients
        }
    }

    # Ajouter le plat au fichier de commande
    commandes_path = os.path.join(get_archive_folder_path().get(), "commandes")
    logs_path = os.path.join(get_archive_folder_path().get(), "logs")
    ajouter_ou_mettre_a_jour_commande(commandes_path, logs_path, plat)

    # Réinitialiser la recette après l'ajout
    if recette and isinstance(recette, dict):
        recette.clear()

    # Fermer la fenêtre de personnalisation
    fenetre_pizza_2.destroy()

# == Interface grillade == #
def perso_grillade(root):
    """
    Interface pour personnaliser une grillade.
    """
    def creation_fenetre():
        # Charger les données du stock
        stock_data = charger_donnees_stock(get_stock_file_path().get())
        viandes_disponibles = stock_data.get("Plats", {}).get("Grillades", {})
        accompagnements_disponibles = stock_data.get("Accompagnement", {})
        accompagnements_disponibles = ["Sans"] + [acc for acc, data in accompagnements_disponibles.items() if not data.get("OutOfStock", False)]

        # Crée une fenêtre pour la personnalisation
        fenetre_grillade = tk.Toplevel(root)
        fenetre_grillade.title("Grillade")
        fenetre_grillade.configure(bg="#2b2b2b")
        fenetre_grillade.attributes("-topmost", True)  # Garde la fenêtre au premier plan

        # Variables pour suivre les quantités de viandes
        quantites_viandes = {viande: tk.IntVar(value=0) for viande in viandes_disponibles}

        # Variable pour l'accompagnement sélectionné
        accompagnement_selectionne = tk.StringVar(value="Frites")

        # Fonction pour ajuster les quantités
        def ajuster_quantite(viande, delta):
            """
            Ajuste la quantité de viande sélectionnée en respectant la limite totale de 2 portions
            et empêche les valeurs négatives.
            """
            # Récupère la valeur de la viande depuis le dictionnaire
            valeur_viande = viandes_disponibles.get(viande, {}).get("Valeur", 0)
            
            # Calcule le total actuel en fonction des quantités et des valeurs des viandes
            total_actuel = sum(
                quantites_viandes[v].get() * viandes_disponibles.get(v, {}).get("Valeur", 0)
                for v in quantites_viandes
            )

            # Calcule la nouvelle valeur
            nouvelle_valeur = quantites_viandes[viande].get() + delta

            # Vérifie que la nouvelle valeur est positive et que le total ne dépasse pas 2 portions
            if 0 <= nouvelle_valeur <= 2 and 0 <= nouvelle_valeur * valeur_viande + total_actuel - quantites_viandes[viande].get() * valeur_viande <= 2:
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
                width=15  # Uniformiser la largeur
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")  # Positionner côte à côte

        # Bouton pour valider la personnalisation
        def valider_grillade():
            """
            Valide la personnalisation de la grillade et ajoute la commande au fichier.
            """
            # Récupérer les viandes choisies et leurs quantités
            viandes_choisies = {viande: quantites_viandes[viande].get() for viande in viandes_disponibles if quantites_viandes[viande].get() > 0}
            accompagnement = accompagnement_selectionne.get()

            if not viandes_choisies:
                messagebox.showerror("Erreur", "Veuillez sélectionner au moins une viande.")
                return

            # Construire le message pour la commande
            if accompagnement == "Sans":
                message = f"Grillade : {' et '.join([f'{q} {v}' for v, q in viandes_choisies.items()])} sans accompagnement"
            else:
                message = f"Grillade : {' et '.join([f'{q} {v}' for v, q in viandes_choisies.items()])} avec {accompagnement}"

            # Charger le prix des pizzas depuis le fichier menu
            menu_data = charger_donnees_menu(get_menu_file_path().get())
            prix_grillade = menu_data.get("Grillade", {}).get("Prix", 0)

            # Préparer les données du plat
            plat = {
                "Nom": message,
                "Statut": "En attente",
                "Prix": prix_grillade,  # Vous pouvez ajouter une logique pour calculer le prix en fonction des viandes et de l'accompagnement
                "Composition": {
                    "Viandes": viandes_choisies,
                    "Accompagnement": accompagnement
                }
            }

            # Charger les données nécessaires pour la commande
            commandes_path = os.path.join(get_archive_folder_path().get(), "commandes")
            logs_path = os.path.join(get_archive_folder_path().get(), "logs")

            # Ajouter ou mettre à jour la commande
            ajouter_ou_mettre_a_jour_commande(commandes_path, logs_path, plat)

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

        # Retourner la fenêtre créée
        return fenetre_grillade

    # Utiliser la fonction pour ouvrir une fenêtre unique
    ouvrir_fenetre_unique("Grillade", creation_fenetre, fermer_autres=True)

# == Interface salades composées == #
def perso_salade_composee(root):
    """
    Interface pour personnaliser une salade composée.
    """
    def creation_fenetre():
        # Charger les données du stock
        stock_data = charger_donnees_stock(get_stock_file_path().get())
        ingredients_disponibles = {
            categorie: {
                ingredient: data for ingredient, data in ingredients.items() if not data.get("OutOfStock", False)
            }
            for categorie, ingredients in stock_data.get("Ingrédients", {}).items()
        }
        ingredients_selectionnes = {
            ingredient: tk.BooleanVar(value=False)
            for categorie, ingredients in ingredients_disponibles.items()
            for ingredient in ingredients
        }

        # Crée une fenêtre pour la personnalisation
        fenetre_salade = tk.Toplevel(root)
        fenetre_salade.title("Salade composée")
        fenetre_salade.configure(bg="#2b2b2b")
        fenetre_salade.attributes("-topmost", True)  # Garde la fenêtre au premier plan

        # Affichage des ingrédients
        ttk.Label(
            fenetre_salade,
            text="Choisissez vos ingrédients :",
            font=("Cambria", 14),
            background="#2b2b2b",
            foreground="white"
        ).pack(pady=10)

        frame_ingredients = ttk.Frame(fenetre_salade)
        frame_ingredients.pack(pady=10)

        row = 0
        for categorie, ingredients in ingredients_disponibles.items():
            # Ajouter un titre pour chaque catégorie
            ttk.Label(
                frame_ingredients,
                text=categorie,
                font=("Cambria", 10, "bold"),
                background="#2b2b2b",
                foreground="white"
            ).grid(row=row, column=0, padx=5, pady=5, sticky="w")
            row += 1

            # Ajouter les ingrédients de la catégorie
            for ingredient in ingredients:
                ttk.Checkbutton(
                    frame_ingredients,
                    text=ingredient,
                    variable=ingredients_selectionnes[ingredient],
                    style="TCheckbutton",
                    width=20
                ).grid(row=row, column=0, padx=5, pady=5, sticky="w")
                row += 1

        # Bouton pour valider la personnalisation
        def valider_salade():
            """
            Valide la personnalisation de la salade composée et ajoute la commande au fichier.
            """
            # Récupérer les ingrédients choisis
            ingredients_choisis = [ingredient for ingredient, var in ingredients_selectionnes.items() if var.get()]

            if not ingredients_choisis:
                messagebox.showerror("Erreur", "Veuillez sélectionner au moins un ingrédient.")
                return

            # Construire le message pour la commande
            message = f"Salade composée avec {', '.join(ingredients_choisis)}"

            # Charger le prix des salades depuis le fichier menu
            menu_data = charger_donnees_menu(get_menu_file_path().get())
            prix_salade = menu_data.get("Salade composée", {}).get("Prix", 0)

            # Préparer les données du plat
            plat = {
                "Nom": message,
                "Statut": "En attente",
                "Prix": prix_salade,
                "Composition": {
                    "Ingrédients": ingredients_choisis
                }
            }

            # Charger les chemins nécessaires pour la commande
            commandes_path = os.path.join(get_archive_folder_path().get(), "commandes")
            logs_path = os.path.join(get_archive_folder_path().get(), "logs")

            # Ajouter ou mettre à jour la commande
            ajouter_ou_mettre_a_jour_commande(commandes_path, logs_path, plat)

            # Fermer la fenêtre
            fenetre_salade.destroy()

        ttk.Button(
            fenetre_salade,
            text="Valider",
            command=valider_salade
        ).pack(pady=20)

        # Ajuster automatiquement la taille de la fenêtre
        fenetre_salade.update_idletasks()
        fenetre_salade.geometry("")

        return fenetre_salade

    # Utiliser la fonction pour ouvrir une fenêtre unique
    ouvrir_fenetre_unique("Salade composée", creation_fenetre, fermer_autres=True)

# == Interface frites == #
def perso_frites(root):
    travaux_en_cours(root)

# === Support === #
# == Interface gestion des stocks == #
def gestion_stock(root):
    """
    Interface pour gérer les stocks avec des catégories en onglets.
    """
    def creation_fenetre():
        # Charger les données du stock
        stock_data = charger_donnees_stock(get_stock_file_path().get())

        # Crée une fenêtre pour la gestion des stocks
        fenetre_stock = tk.Toplevel(root)
        fenetre_stock.title("Gestion des stocks")
        fenetre_stock.configure(bg="#2b2b2b")
        fenetre_stock.attributes("-topmost", True)  # Garde la fenêtre au premier plan

        # Titre principal
        ttk.Label(
            fenetre_stock,
            text="Stock",
            font=("Cambria", 16, "bold"),
            background="#2b2b2b",
            foreground="white"
        ).pack(pady=10)

        # Créer un Notebook pour les onglets
        notebook = ttk.Notebook(fenetre_stock)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet "Plats"
        if "Plats" in stock_data:
            tab_plats = ttk.Frame(notebook)
            notebook.add(tab_plats, text="Plats")

            # Détails des pizzas
            if "Pizza" in stock_data["Plats"]:
                frame_pizza = ttk.LabelFrame(tab_plats, text="Pizzas", padding=10)
                frame_pizza.pack(fill="both", expand=True, padx=10, pady=10)

                for pizza, data in stock_data["Plats"]["Pizza"].items():
                    ttk.Label(
                        frame_pizza,
                        text=pizza,
                        font=("Cambria", 10),
                        width=20,
                        anchor="w"
                    ).grid(row=0, column=0, padx=5, pady=5)

                    quantite = tk.IntVar(value=data.get("Quantité", 0))
                    out_of_stock = tk.BooleanVar(value=data.get("OutOfStock", False))

                    ttk.Checkbutton(
                        frame_pizza,
                        text="Out of Stock",
                        variable=out_of_stock,
                        style="TCheckbutton"
                    ).grid(row=0, column=1, padx=5)

            # Détails des grillades
            if "Grillades" in stock_data["Plats"]:
                frame_grillades = ttk.LabelFrame(tab_plats, text="Grillades", padding=10)
                frame_grillades.pack(fill="both", expand=True, padx=10, pady=10)

                for grillade, data in stock_data["Plats"]["Grillades"].items():
                    ttk.Label(
                        frame_grillades,
                        text=grillade,
                        font=("Cambria", 10),
                        width=20,
                        anchor="w"
                    ).grid(row=0, column=0, padx=5, pady=5)

                    quantite = tk.IntVar(value=data.get("Quantité", 0))
                    out_of_stock = tk.BooleanVar(value=data.get("OutOfStock", False))

                    ttk.Checkbutton(
                        frame_grillades,
                        text="Out of Stock",
                        variable=out_of_stock,
                        style="TCheckbutton"
                    ).grid(row=0, column=1, padx=5)

        # Onglet "Accompagnement"
        if "Accompagnement" in stock_data:
            tab_accompagnement = ttk.Frame(notebook)
            notebook.add(tab_accompagnement, text="Accompagnement")

            frame_accompagnement = ttk.Frame(tab_accompagnement)
            frame_accompagnement.pack(fill="both", expand=True, padx=20, pady=20)

            row = 0
            for accompagnement, data in stock_data["Accompagnement"].items():
                ttk.Label(
                    frame_accompagnement,
                    text=accompagnement,
                    font=("Cambria", 10),
                    width=20,
                    anchor="w"
                ).grid(row=row, column=0, padx=5, pady=5)

                quantite = tk.IntVar(value=data.get("Quantité", 0))
                out_of_stock = tk.BooleanVar(value=data.get("OutOfStock", False))

                ttk.Checkbutton(
                    frame_accompagnement,
                    text="Out of Stock",
                    variable=out_of_stock,
                    style="TCheckbutton"
                ).grid(row=row, column=1, padx=5)

                row += 1

        # Onglet "Ingrédients"
        if "Ingrédients" in stock_data:
            tab_ingredients = ttk.Frame(notebook)
            notebook.add(tab_ingredients, text="Ingrédients")

            frame_ingredients = ttk.Frame(tab_ingredients)
            frame_ingredients.pack(fill="both", expand=True, padx=20, pady=20)

            row = 0
            for categorie, ingredients in stock_data["Ingrédients"].items():
                ttk.Label(
                    frame_ingredients,
                    text=categorie,
                    font=("Cambria", 12, "bold"),
                    background="#2b2b2b",
                    foreground="white"
                ).grid(row=row, column=0, padx=5, pady=5, sticky="w")
                row += 1

                for ingredient, data in ingredients.items():
                    ttk.Label(
                        frame_ingredients,
                        text=ingredient,
                        font=("Cambria", 10),
                        width=20,
                        anchor="w"
                    ).grid(row=row, column=0, padx=5, pady=5)

                    out_of_stock = tk.BooleanVar(value=data.get("OutOfStock", False))

                    ttk.Checkbutton(
                        frame_ingredients,
                        text="Out of Stock",
                        variable=out_of_stock,
                        style="TCheckbutton"
                    ).grid(row=row, column=1, padx=5)

                    row += 1

        # Bouton pour sauvegarder les modifications
        def sauvegarder():
            # Mettre à jour les données du stock
            for categorie, elements in stock_data.items():
                for element, data in elements.items():
                    data["Quantité"] = quantite.get()
                    data["OutOfStock"] = out_of_stock.get()
            sauvegarder_chemin_stock(stock_data)
            fenetre_stock.destroy()

        ttk.Button(
            fenetre_stock,
            text="Sauvegarder",
            command=sauvegarder
        ).pack(pady=20)

        # Ajuster automatiquement la taille de la fenêtre
        fenetre_stock.update_idletasks()
        fenetre_stock.geometry("")

        return fenetre_stock

    # Utiliser la fonction pour ouvrir une fenêtre unique
    ouvrir_fenetre_unique("Gestion des stocks", creation_fenetre, fermer_autres=True)
