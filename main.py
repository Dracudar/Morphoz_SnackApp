'''
Point d'entrée de l'application SnackApp
'''

# Importer la fonction menu_initialisation depuis front.py
from front import menu_initialisation

def main():
    '''
    Point d'entrée principal de l'application.
    '''
    # Lancer le menu d'initialisation
    menu_initialisation()

# Vérifier si le script est exécuté directement
if __name__ == "__main__":
    main()
