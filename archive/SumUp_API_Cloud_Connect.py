"""
Fonctionnalité de paiement par carte bancaire via l'API SumUp.
"""

import requests  # Pour envoyer des requêtes HTTP à l'API SumUp
from dotenv import load_dotenv  # Pour charger les variables d'environnement depuis un fichier .env
import os  # Pour manipuler les chemins de fichiers et les répertoires
import json  # Pour manipuler les données JSON
import datetime  # Pour gérer les dates et heures
from ..src.backend.commandes_utils import charger_fichier_commande  # Pour charger le fichier de commande JSON
from ..src.backend.commandes_saisie_gestion import valider_commande  # Pour valider la commande après paiement et imprimer les tickets

# Ecrire un log de paiement dans un fichier texte
def log_paiement_txt(context, reference, total, devise, resultat):
    logs_dir = os.path.join(context.paths["archive"], "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "SumUp.txt")
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{now}\n  Commande : {reference}\n  Montant : {total} {devise}\n  {resultat}\n\n")

def paiement_SumUp(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):

    # Charger la commande depuis le fichier JSON
    commande = charger_fichier_commande(chemin_fichier)
    total = commande["Informations"]["Montant"]
    devise = commande["Informations"]["Devise"]
    reference = commande["Informations"]["ID"]

    # Configuration SumUp
    TEST_MODE = True  # Mettre à True pour l'environnement de test, False pour la production

    load_dotenv()  # Charge les variables d'environnement depuis le fichier .env
    if TEST_MODE == True:
        API_KEY = os.environ["SUMUP_TEST_API_KEY"]  # Clé API pour l'environnement de test
        MERCHANT_CODE = os.environ["SUMUP_TEST_MERCHANT_CODE"]  # Code marchand pour l'environnement de test
    else:
        API_KEY = os.environ["SUMUP_API_KEY"]  # Clé API pour l'environnement de production
        MERCHANT_CODE = os.environ["MERCHANT_CODE"]  # Code marchand pour l'environnement de production

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "amount": total,
        "currency": devise,
        "checkout_reference": reference,
        "description": "Paiement snack MegaSouye",
        "merchant_code": MERCHANT_CODE
    }

    # Envoyer la requête de paiement à l'API SumUp
    API_URL = "https://api.sumup.com/v0.1/checkouts"  # URL de l'API SumUp pour les paiements
    response = requests.post(API_URL, headers=headers, json=data)  

    # Vérifier la réponse de l'API
    if response.status_code == 201:
        log_paiement_txt(context, reference, total, devise, "Paiement validé")  # Met à jour le log de paiement
        commande["Informations"]["Type de paiement"] = "Carte"  # Met à jour le type de paiement dans la commande
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande, f, indent=4, ensure_ascii=False)

        valider_commande(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées)

    else:
        erreur = response.json()
        log_paiement_txt(context, reference, total, devise, f"Erreur : {erreur}")  # Met à jour le log de paiement avec l'erreur
        from tkinter import messagebox
        messagebox.showerror("Erreur paiement", f"Erreur lors de l'envoi du paiement : {erreur}")  # Affiche un message d'erreur

        return