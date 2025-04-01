'''
Code GUI de l'application SnackApp de Morphoz
'''

### Importer les modules nécessaires
# Modules pour l'interface graphique
import tkinter as tk
from tkinter import ttk
# Fonctions back-end
from Morphoz_SnackApp.back import stock, decremente_stock
from Morphoz_SnackApp.utils import sauvegarder_stock, enregistrer_commande

### Variables globales

# Liste des commandes en cours
commandes_en_cours = []

# Configuration de la fenêtre principale
root = tk.Tk()
root.title("Nouvelle commande")
root.geometry("800x600")

# Création des sections
section_principale = ttk.Frame(root, width=500, height=600)
section_principale.pack(side="left", fill="both", expand=True)

section_droite = ttk.Frame(root, width=300, height=600)
section_droite.pack(side="right", fill="y")

# Variables pour la personnalisation
base_var = tk.StringVar(value="")
ingredient_vars = {}

# Variables pour la gestion des stocks
stock_vars = {}

### Interface principale
def afficher_categories():
    # Effacer la section principale
    for widget in section_principale.winfo_children():
        widget.destroy()

    # Boutons pour les catégories principales
    ttk.Button(section_principale, text="Pizza", command=afficher_recettes_pizza).grid(row=0, column=0, sticky="w")
    ttk.Button(section_principale, text="Grillade").grid(row=1, column=0, sticky="w")
    ttk.Button(section_principale, text="Accompagnement").grid(row=2, column=0, sticky="w")
    ttk.Button(section_principale, text="Gestion des stocks", command=afficher_gestion_stock).grid(row=3, column=0, sticky="w")

### Interface gestion des stocks
def afficher_gestion_stock():
    # Effacer la section principale
    for widget in section_principale.winfo_children():
        widget.destroy()

    # Afficher les stocks actuels
    ttk.Label(section_principale, text="Gestion des stocks :").grid(row=0, column=0, columnspan=3, sticky="w")
    for i, (ingredient, data) in enumerate(stock.items()):
        ttk.Label(section_principale, text=f"{ingredient} :").grid(row=i+1, column=0, sticky="w")
        quantite_var = tk.IntVar(value=data["Quantité"])
        ttk.Entry(section_principale, textvariable=quantite_var, width=5).grid(row=i+1, column=1, sticky="w")
        stock_vars[ingredient] = quantite_var

        out_of_stock_var = tk.BooleanVar(value=data["OutOfStock"])
        ttk.Checkbutton(section_principale, text="Out of Stock", variable=out_of_stock_var).grid(row=i+1, column=2, sticky="w")
        stock_vars[f"{ingredient}_OutOfStock"] = out_of_stock_var

    # Boutons pour sauvegarder les stocks et retourner au menu principal
    ttk.Button(section_principale, text="Sauvegarder", command=sauvegarder_stock).grid(row=len(stock)+1, column=0, columnspan=3)
    ttk.Button(section_principale, text="Retour", command=afficher_categories).grid(row=len(stock)+2, column=0, columnspan=3)

def sauvegarder_stock():
    for ingredient, var in stock_vars.items():
        if "_OutOfStock" in ingredient:
            stock[ingredient.replace("_OutOfStock", "")]["OutOfStock"] = var.get()
        else:
            stock[ingredient]["Quantité"] = var.get()
    sauvegarder_stock(stock, "stock.json")  # Sauvegarder dans un fichier JSON
    afficher_categories()  # Retour au menu principal après sauvegarde

### Interface gestion des commandes
def afficher_commandes_en_cours():
    # Effacer la section des commandes en cours
    for widget in section_droite.winfo_children():
        widget.destroy()

    # Afficher les commandes en cours
    ttk.Label(section_droite, text="Commandes en cours :").pack(anchor="w")
    for commande in commandes_en_cours:
        frame = ttk.Frame(section_droite)
        frame.pack(fill="x", pady=2)
        ttk.Label(frame, text=f"{commande['type']} - {commande['details']}").pack(side="left")
        ttk.Button(frame, text="Valider", command=lambda cid=commande["id"]: valider_commande(cid)).pack(side="right")

def valider_commande(commande_id):
    global commandes_en_cours
    commande = next(cmd for cmd in commandes_en_cours if cmd["id"] == commande_id)
    try:
        decremente_stock(commande["details"]["Ingrédients"])
        enregistrer_commande(commande, "commandes.log")  # Enregistrer la commande dans un fichier log
        commandes_en_cours = [cmd for cmd in commandes_en_cours if cmd["id"] != commande_id]
        afficher_commandes_en_cours()
    except ValueError as e:
        print(e)

### Interface gestion des pizzas
def afficher_recettes_pizza():
    # Effacer la section principale
    for widget in section_principale.winfo_children():
        widget.destroy()

    # Charger le menu si nécessaire
    from Morphoz_SnackApp.back import menu, charger_menu
    if menu is None:
        charger_menu("carte_MS8.json")

    # Section pour choisir une recette
    ttk.Label(section_principale, text="Choisissez une recette :").grid(row=0, column=0, sticky="w")
    for i, recipe in enumerate(menu["Pizza"]["Recettes"]):
        ttk.Button(section_principale, text=recipe, command=lambda r=recipe: afficher_personnalisation_pizza(r)).grid(row=i+1, column=0, sticky="w")

    # Bouton pour retourner au menu principal
    ttk.Button(section_principale, text="Annuler", command=afficher_categories).grid(row=len(menu["Pizza"]["Recettes"])+1, column=0, sticky="w")

def afficher_personnalisation_pizza(recipe):
    # Effacer la section principale
    for widget in section_principale.winfo_children():
        widget.destroy()

    # Section pour choisir une base
    ttk.Label(section_principale, text="Choisissez une base :").grid(row=0, column=0, sticky="w")
    base_var.set("")
    for i, base in enumerate(menu["Pizza"]["Base"]):
        ttk.Radiobutton(section_principale, text=base, variable=base_var, value=base).grid(row=i+1, column=0, sticky="w")

    # Section pour choisir les ingrédients
    ttk.Label(section_principale, text="Choisissez vos ingrédients :").grid(row=0, column=1, sticky="w")
    for i, ingredient in enumerate(menu["Pizza"]["Ingrédients"]):
        var = tk.BooleanVar(value=ingredient in menu["Pizza"]["Recettes"][recipe]["Ingrédients"])
        ingredient_vars[ingredient] = var
        ttk.Checkbutton(section_principale, text=ingredient, variable=var).grid(row=i+1, column=1, sticky="w")

    # Boutons pour soumettre ou annuler la commande
    ttk.Button(section_principale, text="Soumettre la commande", command=submit_pizza_order).grid(row=len(menu["Pizza"]["Ingrédients"])+2, column=0, columnspan=2)
    ttk.Button(section_principale, text="Annuler", command=afficher_categories).grid(row=len(menu["Pizza"]["Ingrédients"])+3, column=0, columnspan=2)

def submit_pizza_order():
    selected_base = base_var.get()
    selected_ingredients = [ingredient for ingredient, var in ingredient_vars.items() if var.get()]
    try:
        # Décompter uniquement la "Pâte à pizza"
        decremente_stock(["Pâte à pizza"])
        commandes_en_cours.append({
            "id": len(commandes_en_cours) + 1,
            "type": "Pizza",
            "details": {"Base": selected_base, "Ingrédients": selected_ingredients}
        })
        afficher_categories()  # Retour au menu principal après enregistrement
    except ValueError as e:
        print(e)

# Afficher les catégories principales et les commandes en cours
afficher_categories()
afficher_commandes_en_cours()

# Lancer l'interface graphique
root.mainloop()
