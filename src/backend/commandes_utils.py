'''
Module d'utilitaires pour la gestion des commandes
- Génération d'un identifiant unique
- Chargement de fichiers JSON avec gestion des erreurs
'''

import os
from datetime import datetime
import json

def generer_identifiant_commande(logs_path, commandes_path):
    """
    Génère un identifiant unique pour une commande au format aaaammjj-000.

    :param logs_path: Chemin vers le dossier des logs.
    :param commandes_path: Chemin vers le dossier des commandes.
    :return: Identifiant unique de la commande.
    """
    date_actuelle = datetime.now().strftime("%Y%m%d")  # aaaammjj
    log_file = os.path.join(logs_path, "dernier_id.json")

    # Vérifier si le fichier de log existe
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as fichier:
            dernier_id = json.load(fichier).get(date_actuelle, 0)
    else:
        dernier_id = 0

    # Incrémenter l'identifiant
    nouvel_id = dernier_id + 1

    # Mettre à jour le fichier de log
    with open(log_file, "w", encoding="utf-8") as fichier:
        json.dump({date_actuelle: nouvel_id}, fichier, indent=4)

    # Retourner l'identifiant au format aaaammjj-000
    return f"{date_actuelle}-{nouvel_id:03d}"

def charger_fichier_json(chemin_fichier):
    """
    Charge un fichier JSON avec gestion des erreurs.

    :param chemin_fichier: Chemin vers le fichier JSON.
    :return: Contenu du fichier sous forme de dictionnaire ou None si une erreur survient.
    """
    if not os.path.exists(chemin_fichier):
        print(f"Erreur : Le fichier '{chemin_fichier}' est introuvable.")
        return None

    try:
        with open(chemin_fichier, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier '{chemin_fichier}' contient des données invalides.")
        # Déplacer le fichier corrompu dans un dossier dédié
        dossier_corrompu = os.path.join(os.path.dirname(chemin_fichier), "corrompu")
        os.makedirs(dossier_corrompu, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_corrompu, os.path.basename(chemin_fichier)))
        return None
