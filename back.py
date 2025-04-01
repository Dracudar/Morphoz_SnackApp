'''
Code Back-end de l'application SnackApp de Morphoz
'''

# Emplacement par défaut du fichier carte

import json

def lire_menu(fichier):
    """Lit le fichier JSON contenant le menu et retourne son contenu."""
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            menu = json.load(f)
        return menu
    except FileNotFoundError:
        print(f"Le fichier {fichier} est introuvable.")
    except json.JSONDecodeError:
        print(f"Erreur lors du décodage du fichier {fichier}.")
    return None

# Initialisation des variables globales
menu = None  # Contiendra le menu chargé depuis un fichier JSON
stock = {}   # Contiendra le stock chargé depuis un fichier JSON

def charger_menu(fichier_menu):
    """Charge un fichier JSON contenant le menu et met à jour la variable globale menu."""
    global menu
    try:
        with open(fichier_menu, "r", encoding="utf-8") as f:
            menu = json.load(f)
    except FileNotFoundError:
        print(f"Le fichier {fichier_menu} est introuvable.")
    except json.JSONDecodeError:
        print(f"Erreur lors du décodage du fichier {fichier_menu}.")

def charger_stock(fichier_stock):
    """Charge un fichier JSON contenant le stock et met à jour la variable globale stock."""
    global stock
    try:
        with open(fichier_stock, "r", encoding="utf-8") as f:
            stock = json.load(f)
    except FileNotFoundError:
        print(f"Le fichier {fichier_stock} est introuvable.")
    except json.JSONDecodeError:
        print(f"Erreur lors du décodage du fichier {fichier_stock}.")

def decremente_stock(ingredients):
    """Décrémente le stock pour une liste d'ingrédients."""
    for ingredient in ingredients:
        if ingredient in stock:
            stock[ingredient]["Quantité"] -= 1
            if stock[ingredient]["Quantité"] < 0:
                stock[ingredient]["Quantité"] = 0
        else:
            raise ValueError(f"L'ingrédient {ingredient} est introuvable dans le stock.")

# Exemple d'utilisation
if __name__ == "__main__":
    fichier_menu = "carte_MS8.json"
    fichier_stock = "stock.json"
    charger_menu(fichier_menu)
    charger_stock(fichier_stock)
    if menu:
        print("Contenu du menu :")
        print(json.dumps(menu, indent=4, ensure_ascii=False))
    if stock:
        print("Contenu du stock :")
        print(json.dumps(stock, indent=4, ensure_ascii=False))