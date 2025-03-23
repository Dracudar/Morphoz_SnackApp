'''
Point d'entrée de l'application SnackApp
'''

# Importer les modules nécessaires
from Morphoz_SnackApp.front import root, afficher_categories, afficher_commandes_en_cours

# Initialiser l'interface graphique
if __name__ == "__main__":
    # Afficher les catégories principales et les commandes en cours
    afficher_categories()
    afficher_commandes_en_cours()

    # Lancer l'application
    root.mainloop()