'''
Code Back-end de l'application SnackApp de Morphoz
'''

from Morphoz_SnackApp.utils import charger_stock, sauvegarder_stock, charger_menu, sauvegarder_menu
import json

### Gestion du stock de MP
stock = charger_stock("stock.json")

def decremente_stock(ingredients):
    for ingredient in ingredients:
        if not est_en_stock(stock, ingredient):
            raise ValueError(f"{ingredient} est en rupture de stock.")
        stock[ingredient]["Quantité"] -= 1
    sauvegarder_stock(stock, "stock.json")

def charger_recettes(fichier):
    """Charge les recettes depuis un fichier JSON."""
    with open(fichier, "r", encoding="utf-8") as f:
        return json.load(f)

# Exemple d'utilisation des recettes
recettes = charger_recettes("carte_MS8.json")

### Système de prise de commande
menu = charger_menu("menu.json")

# Sauvegarder le menu si nécessaire
# sauvegarder_menu(menu, "menu.json")
