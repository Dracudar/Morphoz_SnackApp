'''
Sous-fichier comprenant diverses fonctions utilitaires pour le projet SnackApp.
'''
### Importer les modules nécessaires
import json
from datetime import datetime
from tkinter import filedialog

#### Fonctions utilitaires
## Fonction pour charger un fichier JSON
def chercher_fichier():
    '''Ouvre un explorateur de fichiers pour sélectionner un fichier JSON.'''
    filepath = filedialog.askopenfilename(
        filetypes=[("Fichiers JSON", "*.json")],
        title="Sélectionner un fichier JSON"
    )
    return filepath
