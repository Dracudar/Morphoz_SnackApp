'''
Code UI pour l'interface temporaire de personnalisation des pizzas
'''

# === Importer les modules nécessaires === #
# == Fonctions utilitaires et de configuration == #
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

# === Personnalisation des plats === #
# == Interface pizza == #
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
        "Type": "Pizza",
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