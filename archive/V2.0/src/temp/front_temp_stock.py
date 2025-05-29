'''
Code UI pour les interfaces temporaire de gestion des stocks
'''

# === Importer les modules nécessaires === #
from src.utils import (
    charger_donnees_stock
    )
from src.utils import (
    get_stock_file_path,
    get_archive_folder_path
    )
from src.back import ajouter_ou_mettre_a_jour_commande
import os  # Pour manipuler les chemins de fichiers

# == Modules graphiques == #
from UI.front import * # Modules Tinker
from src.front_temp import * # Modules de gestion des fenêtres

# === Affichage === #
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
