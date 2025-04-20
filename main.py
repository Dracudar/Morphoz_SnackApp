'''
Point d'entrée de l'application SnackApp
'''

# Importer la fonction menu_initialisation depuis front.py
from src.front import menu_selection

def main(): # Point d'entrée principal de l'application.
    menu_selection()

# Vérifier si le script est exécuté directement
if __name__ == "__main__":
    main()
