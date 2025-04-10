'''
Sous-fichier comprenant diverses fonctions utilitaires pour le projet SnackApp.
'''
### Importer les modules nécessaires
import json
import os
from datetime import datetime
from tkinter import filedialog

# Définir le chemin absolu pour config.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Répertoire du fichier utils.py
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

#### Fonctions utilitaires
## Fonction pour charger un fichier JSON
def chercher_fichier():
    '''Ouvre un explorateur de fichiers pour sélectionner un fichier JSON.'''
    filepath = filedialog.askopenfilename(
        filetypes=[("Fichiers JSON", "*.json")],
        title="Sélectionner un fichier JSON"
    )
    return filepath

def sauvegarder_chemins(stock_path, menu_path):
    """Sauvegarde les chemins des fichiers JSON dans un fichier de configuration."""
    data = {
        "stock_file": stock_path,
        "menu_file": menu_path
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def charger_chemins():
    """Charge les chemins des fichiers JSON depuis un fichier de configuration."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"stock_file": "", "menu_file": ""}
