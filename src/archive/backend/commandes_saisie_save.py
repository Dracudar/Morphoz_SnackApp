'''
Fonction permettant de créer ou mettre à jour le fichier JSON de la commande en cours de saisie.
'''

import os
import json
from datetime import datetime
from collections import OrderedDict
from .commandes_utils import charger_fichier_commande, generer_ID_commande
    
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
    fichiers_commandes = [
        f for f in os.listdir(commandes_path) if f.startswith("commande_")
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
        nouvel_id = generer_ID_commande(logs_path, commandes_path)
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