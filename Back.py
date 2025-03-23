'''
Code Back-end de l'application SnackApp de Morphoz
'''

### Importer les modules nécessaires


### Gestion du stock de MP
stock = {
    "Pâte à pizza": 50,
    "Poitrine": 50,
    "Chipolatta": 50,
    "Merguez": 50,
    "Steak vegé": 50,
    "Frites": 50,
    "Légumes": 50
}

def decremente_stock(ingredients):
    for ingredient in ingredients:
        if ingredient in stock and stock[ingredient] > 0:
                            stock[ingredient] -= 1
        else:
            raise ValueError(f"Stock insuffisant pour {ingredient}")

### Système de prise de commande
menu = {
    "Pizza": {
        "Base": ["Tomate", "Crème"],
        "Ingrédients": ["Mozzarella", "Basilic", "Pepperoni", "Champignons", "Olives", "Jambon"],
        "Recettes": {
            "Personnalisable": {"Base": [], "Ingrédients": []},
            "Margherita": {"Base": ["Tomate"], "Ingrédients": ["Mozzarella", "Basilic"]},
        }
    },
    "Grillade": {
        "Viande(s)": ["Poitrine", "Chipolatta", "Merguez", "Steak vegé"],
        "Accompagnement": ["Frites", "Légumes"]
    },
    "Accompagnement seul": {
        "Frites": {},
        "Légumes": {}
    }
}
