"""
Code UI pour les interfaces temporaire de l'application SnackApp :
- Personnalisation des pizzas
- Personnalisation des grillades
- Personnalisation des salades composées
- Gestion des stocks
"""

# === Importer les modules nécessaires === #
# == Fonctions utilitaires et de configuration == #
from src.utils import (
    charger_donnees_menu, 
    get_menu_file_path,
)
from src.utils import (
    get_stock_file_path,
    charger_donnees_stock,
    sauvegarder_chemin_stock
)
from functools import partial

# == Modules graphiques == #
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Variable globale pour suivre les fenêtres ouvertes
fenetres_ouvertes = {}

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
    Valide la personnalisation de la pizza et affiche les choix sélectionnés.
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

    # Afficher les choix dans la console (ou les sauvegarder pour une commande)
    print(message)

    # Réinitialiser la recette après l'impression
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
            Ajuste la quantité de viande sélectionnée en respectant la limite totale de 2 portions.
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
                width=15  # Uniformiser la largeur
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
            ingredients_choisis = [ingredient for ingredient, var in ingredients_selectionnes.items() if var.get()]
            print(f"Ingrédients choisis : {', '.join(ingredients_choisis)}")
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
    Interface pour gérer les stocks.
    """
    def creation_fenetre():
        # Charger les données du fichier stock.json
        stock_file_path = get_stock_file_path().get()
        stock_data = charger_donnees_stock(stock_file_path)
        plats = stock_data.get("Plats", {})
        ingredients = stock_data.get("Ingrédients", {})

        # Crée une fenêtre pour la gestion des stocks
        fenetre_stock = tk.Toplevel(root)
        fenetre_stock.title("Gestion des Stocks")
        fenetre_stock.configure(bg="#2b2b2b")
        fenetre_stock.attributes("-topmost", True)  # Garde la fenêtre au premier plan

        # Fonction pour ajuster les quantités
        def ajuster_quantite(plat, produit, delta):
            if "Quantité" in plats[plat][produit]:
                plats[plat][produit]["Quantité"] = max(0, plats[plat][produit]["Quantité"] + delta)
                mise_a_jour_interface()

        # Fonction pour basculer le mode "Hors Stock"
        def basculer_hors_stock(plat, etat):
            plats[plat]["OutOfStock"] = etat
            mise_a_jour_interface()

# Fonction pour ouvrir la gestion des ingrédients
        def ouvrir_gestion_ingredients():
            gestion_ingredients(root)

        # Fonction pour mettre à jour l'interface
        def mise_a_jour_interface():
            for plat, produits in plats.items():
                if plat == "Grillades":
                    for produit, data in produits.items():
                        if "Quantité" in data:
                            labels_quantites[plat][produit].config(text=f"Quantité : {data['Quantité']}")
                elif "Quantité" in produits:
                    labels_quantites[plat].config(text=f"Quantité : {produits['Quantité']}")
                if "OutOfStock" in produits:
                    checkbuttons_hors_stock[plat].set(produits.get("OutOfStock", False))

        # Fonction pour sauvegarder les modifications dans le fichier stock.json
        def sauvegarder_stocks():
            try:
                with open(stock_file_path, "w", encoding="utf-8") as fichier:
                    json.dump({"Plats": plats, "Ingrédients": ingredients}, fichier, indent=4, ensure_ascii=False)
                print("Les stocks ont été sauvegardés avec succès.")
            except Exception as e:
                print(f"Erreur lors de la sauvegarde des stocks : {e}")
            fenetre_stock.destroy()

        # Conteneur principal
        frame_principale = ttk.Frame(fenetre_stock, padding=10)
        frame_principale.pack(fill="both", expand=True)

        # Widgets pour chaque plat
        labels_quantites = {}
        checkbuttons_hors_stock = {}

        for plat, produits in plats.items():
            frame_plat = ttk.Frame(frame_principale, padding=5)
            frame_plat.pack(fill="x", pady=5)

            # Nom du plat
            ttk.Label(
                frame_plat,
                text=plat,
                font=("Cambria", 12),
                background="#2b2b2b",
                foreground="white"
            ).pack(side="left", padx=5)

            if plat == "Pizza":
                # Quantité de "Pâte à pizza"
                labels_quantites[plat] = ttk.Label(frame_plat, text=f"Quantité : {produits['Pâte à pizza']['Quantité']}")
                labels_quantites[plat].pack(side="left", padx=5)

                # Boutons de modification de quantité
                ttk.Button(frame_plat, text="-", command=lambda: ajuster_quantite(plat, "Pâte à pizza", -1)).pack(side="left", padx=2)
                ttk.Button(frame_plat, text="+", command=lambda: ajuster_quantite(plat, "Pâte à pizza", 1)).pack(side="left", padx=2)

            elif plat == "Grillades":
                # Sous-catégorie pour les viandes
                for viande, data in produits.items():
                    frame_viande = ttk.Frame(frame_principale, padding=5)
                    frame_viande.pack(fill="x", pady=5)

                    ttk.Label(
                        frame_viande,
                        text=viande,
                        font=("Cambria", 10),
                        background="#2b2b2b",
                        foreground="white"
                    ).pack(side="left", padx=5)

                    labels_quantites[plat] = labels_quantites.get(plat, {})
                    labels_quantites[plat][viande] = ttk.Label(frame_viande, text=f"Quantité : {data['Quantité']}")
                    labels_quantites[plat][viande].pack(side="left", padx=5)

                    ttk.Button(frame_viande, text="-", command=lambda v=viande: ajuster_quantite(plat, v, -1)).pack(side="left", padx=2)
                    ttk.Button(frame_viande, text="+", command=lambda v=viande: ajuster_quantite(plat, v, 1)).pack(side="left", padx=2)

            elif plat in ["Frites", "Légumes"]:
                # Regrouper dans une catégorie "Accompagnement"
                if "Accompagnement" not in labels_quantites:
                    frame_accompagnement = ttk.Frame(frame_principale, padding=5)
                    frame_accompagnement.pack(fill="x", pady=5)

                    ttk.Label(
                        frame_accompagnement,
                        text="Accompagnement",
                        font=("Cambria", 12),
                        background="#2b2b2b",
                        foreground="white"
                    ).pack(side="left", padx=5)

                    labels_quantites["Accompagnement"] = {}

                labels_quantites["Accompagnement"][plat] = ttk.Label(frame_accompagnement, text=f"{plat} : {produits['Quantité']}")
                labels_quantites["Accompagnement"][plat].pack(side="left", padx=5)

                ttk.Button(frame_accompagnement, text="-", command=lambda p=plat: ajuster_quantite(plat, plat, -1)).pack(side="left", padx=2)
                ttk.Button(frame_accompagnement, text="+", command=lambda p=plat: ajuster_quantite(plat, plat, 1)).pack(side="left", padx=2)

        # Bouton pour sauvegarder les modifications
        ttk.Button(
            fenetre_stock,
            text="Sauvegarder",
            style="TButton",
            command=sauvegarder_stocks
        ).pack(pady=20)

        # Ajuster automatiquement la taille de la fenêtre
        fenetre_stock.update_idletasks()
        fenetre_stock.geometry("")

        return fenetre_stock

    # Utiliser la fonction pour ouvrir une fenêtre unique
    ouvrir_fenetre_unique("Gestion des Stocks", creation_fenetre, fermer_autres=False)