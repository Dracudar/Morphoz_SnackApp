# filepath: d:\Projets\Programmation\Morphoz_SnackApp\main.py
import sys
import os

# Ajouter le dossier 'src' au chemin Python
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

'''
Point d'entrée de l'application SnackApp
'''

# Importer la fonction menu_initialisation depuis front.py
from src.front import menu_selection

def main():  # Point d'entrée principal de l'application.
    menu_selection()

# Vérifier si le script est exécuté directement
if __name__ == "__main__":
    main()
