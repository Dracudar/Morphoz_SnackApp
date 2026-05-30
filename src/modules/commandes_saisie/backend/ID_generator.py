#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ID_generator.py

Description:
    Génère un identifiant unique pour une commande au format aaaammjj-000.
    
Author :
    Dracudar

Version: 
    1.0

Date de création : 
    2025.06.02

Date de modification: 
    2026.05.30
"""

import os
from datetime import datetime
import json

def generer_ID_commande(logs_path, commandes_path):
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