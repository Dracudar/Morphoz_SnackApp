import json
from datetime import datetime

def charger_stock(fichier):
    '''Charge les stocks depuis un fichier JSON.'''
    try:
        with open(fichier, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fichier {fichier} introuvable. Initialisation avec un stock vide.")
        return {}

def sauvegarder_stock(stock, fichier):
    '''Sauvegarde les stocks dans un fichier JSON.'''
    with open(fichier, "w") as f:
        json.dump(stock, f, indent=4)
        print(f"Stock sauvegardé dans {fichier}.")

def charger_menu(fichier):
    '''Charge le menu depuis un fichier JSON.'''
    try:
        with open(fichier, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fichier {fichier} introuvable. Initialisation avec un menu vide.")
        return {}

def sauvegarder_menu(menu, fichier):
    '''Sauvegarde le menu dans un fichier JSON.'''
    with open(fichier, "w") as f:
        json.dump(menu, f, indent=4)
        print(f"Menu sauvegardé dans {fichier}.")

def enregistrer_commande(commande, fichier="commandes.log"):
    '''Enregistre une commande dans un fichier texte.'''
    with open(fichier, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {commande}\n")
        print(f"Commande enregistrée : {commande}")