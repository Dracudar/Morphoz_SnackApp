'''
Code UI pour les interfaces temporaire de personnalisation des salades composées
'''

# === Importer les modules nécessaires === #
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