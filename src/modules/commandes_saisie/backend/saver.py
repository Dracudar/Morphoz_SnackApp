#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
saver.py

Description:
    Création et mise à jour du fichier JSON de la commande en cours de saisie.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.02

Date de modification:
    2026.06.03
"""

import os
import json
from datetime import datetime
from collections import OrderedDict
from src.backend.commandes_utils import charger_fichier_commande


def initialiser_dossiers_commandes(commandes_path, logs_path):
    """
    Crée la structure de dossiers nécessaire pour l'enregistrement des commandes.
    Appelée avant chaque sauvegarde pour garantir l'existence des dossiers.

    :param commandes_path: Chemin vers le dossier des commandes
    :param logs_path: Chemin vers le dossier des logs
    """
    os.makedirs(logs_path, exist_ok=True)
    os.makedirs(commandes_path, exist_ok=True)
    os.makedirs(os.path.join(commandes_path, "en_cours"), exist_ok=True)
    os.makedirs(os.path.join(commandes_path, "terminee"), exist_ok=True)
    os.makedirs(os.path.join(commandes_path, "annulee"), exist_ok=True)
    os.makedirs(os.path.join(commandes_path, "corrompu"), exist_ok=True)


def ID_generator(logs_path, commandes_path):
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


# === Gestion des fichiers de commandes === #
def creer_dict_plat(plat_id, plat):
    """
    Crée un dictionnaire représentant un plat, avec le champ 'Recette' inséré
    entre 'Plat' et 'Nom' si le plat est une pizza.
    """
    base_dict = {
        "ID": plat_id,
        "Plat": plat["Plat"],
        "Nom": plat["Nom"],
        "Date de mise en livraison": ["", ""],
        "Date de livraison": ["", ""],
        "Statut": "En attente",
        "Prix": plat["Prix"],
        "Composition": plat["Composition"]
    }
    if plat["Plat"].lower() == "pizza":
        # Réorganiser pour insérer "Recette" entre "Plat" et "Nom"
        return OrderedDict([
            ("ID", base_dict["ID"]),
            ("Plat", base_dict["Plat"]),
            ("Recette", plat.get("Recette", "")),
            ("Nom", base_dict["Nom"]),
            ("Date de mise en livraison", base_dict["Date de mise en livraison"]),
            ("Date de livraison", base_dict["Date de livraison"]),
            ("Statut", base_dict["Statut"]),
            ("Prix", base_dict["Prix"]),
            ("Composition", base_dict["Composition"]),
        ])
    else:
        return base_dict

def MAJ_commande(commandes_path, logs_path, plat):
    """
    Ajoute un plat à une commande existante ou crée une nouvelle commande.

    :param commandes_path: Chemin vers le dossier des commandes.
    :param logs_path: Chemin vers le dossier des logs.
    :param plat: Dictionnaire contenant les informations du plat à ajouter.
    """
    # Initialiser les dossiers si nécessaire
    initialiser_dossiers_commandes(commandes_path, logs_path)

    # Search for existing draft orders in the root commandes folder
    fichiers_commandes = [
        f for f in os.listdir(commandes_path) if f.startswith("commande_") and f.endswith(".json")
    ]

    if fichiers_commandes:
        # Charger le dernier fichier de commande existant
        fichiers_commandes.sort()  # Trier pour obtenir le dernier fichier
        dernier_fichier = fichiers_commandes[-1]
        chemin_fichier = os.path.join(commandes_path, dernier_fichier)

        commande = charger_fichier_commande(chemin_fichier)
        if not commande:
            return

        # Ajouter le plat à la commande
        numero_plat = len(commande["Commande"]) + 1
        plat_id = f"{commande['Informations']['ID']}-{numero_plat:02d}"
        commande["Commande"][f"#{numero_plat:02d}"] = creer_dict_plat(plat_id, plat)

        # Mettre à jour le montant total
        commande["Informations"]["Montant"] = sum(
            p["Prix"] for p in commande["Commande"].values() if p["Statut"] != "Annulé"
        )

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

    else:
        # Créer une nouvelle commande
        nouvel_id = ID_generator(logs_path, commandes_path)
        chemin_fichier = os.path.join(commandes_path, f"commande_{nouvel_id}.json")
        plat_id = f"{nouvel_id}-01"
        nouvelle_commande = {
            "Informations": {
                "ID": nouvel_id,  # Identifiant de la commande au format aaaammjj-000
                "Date de création": [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")],  # Date et heure de création du fichier
                "Date de validation": ["", ""],  # Date et heure où la commande a été payé et validée
                "Date de livraison": ["", ""],  # Date et heure où la totaliré des plats a été livrée
                "Statut": "En saisie",  # Statut de la commande (En saisie, Validée, Terminée, Annulée)
                "Montant": plat["Prix"],  # Montant total de la commande
                "Devise": "EUR",  # Devise de la commande (EUR, USD, etc.), EUR par défaut
                "Type de paiement": "",  # Type de paiement (CB, espèces ou repas gratuits), défini au moment de la validation
                "Contact": ""  # Numéro de téléphone du client, défini au moment de la validation (utilité à voir si l'on connecte le logiciel à un service de SMS pour prévenir lorsqu'un plat est prêt)
            },
            "Commande": {
                "#01": creer_dict_plat(plat_id, plat)
            }
        }

        # Sauvegarder la nouvelle commande
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(nouvelle_commande, fichier, indent=4, ensure_ascii=False)