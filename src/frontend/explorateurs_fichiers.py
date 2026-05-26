'''
Utilitaires pour l'interface graphique - Explorateurs de fichiers
Usage lors de l'initialisation de l'application.
Ces fonctions permettent de sélectionner les fichiers et dossiers nécessaires au fonctionnement.
'''

from tkinter import filedialog

def chercher_fichier_menu():
    '''Ouvre un explorateur de fichiers pour sélectionner un fichier JSON.'''
    filepath = filedialog.askopenfilename(
        filetypes=[("Fichiers JSON", "*.json")],
        title="Sélectionner le fichier du menu"
    )
    return filepath

def chercher_fichier_stock():
    '''Ouvre un explorateur de fichiers pour  sélectionner un fichier JSON.'''
    filepath = filedialog.askopenfilename(
        filetypes=[("Fichiers JSON", "*.json")],
        title="Sélectionner le fichier de stock"
    )
    return filepath

def chercher_dossier():
    """Ouvre un explorateur de fichiers pour sélectionner un dossier."""
    folder_path = filedialog.askdirectory(
        title="Sélectionner le dossier de fonctionnement"
    )
    return folder_path
