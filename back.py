'''
Code Back-end de l'application SnackApp de Morphoz
'''

from Morphoz_SnackApp.utils import charger_stock, sauvegarder_stock, charger_menu, sauvegarder_menu
import json

### Gestion du stock de MP
stock = charger_stock("stock.json")

def decremente_stock(ingredients):
    for ingredient in ingredients:
        # Ne décompter que la "Pâte à pizza" pour les pizzas
        if ingredient == "Pâte à pizza" and stock[ingredient] > 0:
            stock[ingredient] -= 1
        elif ingredient != "Pâte à pizza" and ingredient in stock and stock[ingredient] > 0:
            stock[ingredient] -= 1
        else:
            raise ValueError(f"Stock insuffisant pour {ingredient}")
    sauvegarder_stock(stock, "stock.json")  # Sauvegarder après modification

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
