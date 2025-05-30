'''
Code du backend pour la gestion des commandes et la génération de logs.
'''

# === Import des modules nécessaires === #
import os
from datetime import datetime
import json

# === Définitions === #
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
    
# === Gestion des fichiers de commandes === #
def ajouter_ou_mettre_a_jour_commande(commandes_path, logs_path, plat):
    """
    Ajoute un plat à une commande existante ou crée une nouvelle commande.

    :param commandes_path: Chemin vers le dossier des commandes.
    :param logs_path: Chemin vers le dossier des logs.
    :param plat: Dictionnaire contenant les informations du plat à ajouter.
    """
    date_actuelle = datetime.now().strftime("%Y%m%d")  # aaaammjj
    fichiers_commandes = [
        f for f in os.listdir(commandes_path) if f.startswith(f"commande_{date_actuelle}")
    ]

    if fichiers_commandes:
        # Charger le dernier fichier de commande existant
        fichiers_commandes.sort()  # Trier pour obtenir le dernier fichier
        dernier_fichier = fichiers_commandes[-1]
        chemin_fichier = os.path.join(commandes_path, dernier_fichier)

        commande = charger_fichier_json(chemin_fichier)
        if not commande:
            return

        # Ajouter le plat à la commande
        numero_plat = len(commande["Commande"]) + 1
        plat_id = f"{commande['Informations']['ID']}-{numero_plat:02d}"
        commande["Commande"][f"#{numero_plat:02d}"] = {
            "ID": plat_id,
            "Type": plat["Type"],
            "Nom": plat["Nom"],
            "Statut": "En attente",
            "Prix": plat["Prix"],
            "Composition": plat["Composition"]
        }

        # Mettre à jour le montant total
        commande["Informations"]["Montant"] = sum(
            p["Prix"] for p in commande["Commande"].values() if p["Statut"] != "Annulé"
        )

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

    else:
        # Créer une nouvelle commande
        nouvel_id = generer_identifiant_commande(logs_path, commandes_path)
        chemin_fichier = os.path.join(commandes_path, f"commande_{nouvel_id}.json")

        nouvelle_commande = {
            "Informations": {
                "ID": nouvel_id,  # Identifiant de la commande au format aaaammjj-000
                "Date de création": [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")], # Date et heure de création du fichier
                "Date de validation": ["", ""], # Date et heure où la commande a été payé et validée
                "Date de livraison": ["", ""], # Date et heure où la totaliré des plats a été livrée
                "Statut": "En saisie", # Statut de la commande (En saisie, Validée, Terminée, Annulée)
                "Montant": plat["Prix"], # Montant total de la commande
                "Devise": "EUR", # Devise de la commande (EUR, USD, etc.), EUR par défaut
                "Type de paiement": "", # Type de paiement (CB, espèces ou repas gratuits), défini au moment de la validation
                "Contact": "" # Numéro de téléphone du client, défini au moment de la validation (utilité à voir si l'on connecte le logiciel à un service de SMS pour prévenir lorsqu'un plat est prêt)
            },
            "Commande": {
                "#01": {
                    "ID": f"{nouvel_id}-01", # Identifiant du plat au format aaaammjj-000-01 (regroupement du numéro de la commande et du numéro du plat)
                    "Type": plat["Type"], # Type de plat (Entrée, Plat, Dessert, Boisson)
                    "Nom": plat["Nom"], # Nom du plat permtant de l'identifier dans l'affichage
                    "Date de mise en livraison": ["", ""], # Date et heure où le plat a fini d'être préparé et est mis en livraison
                    "Date de livraison": ["", ""], # Date et heure où le plat a été livré
                    "Statut": "En attente", # Statut du plat (En attente, En préparation, Prêt, Livré, Annulé)
                    "Prix": plat["Prix"], # Prix du plat
                    "Composition": plat["Composition"] # Composition du plat : base, ingrédients, viande, accompagnement, etc. selon le type de plat
                }
            }
        }

        # Sauvegarder la nouvelle commande
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(nouvelle_commande, fichier, indent=4, ensure_ascii=False)

# === Gestion des commandes === #
def valider_commande(chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
    commande = charger_fichier_json(chemin_fichier)
    if not commande:
        return

    # TODO : mettre en place le système de paiement (CB, espèces, repas gratuits) et mettre à jour le type de paiement dans le fichier JSON
    
    # Mettre à jour la date de validation
    commande["Informations"]["Date de validation"] = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]

    # Mettre à jour les statuts
    commande["Informations"]["Statut"] = "Validée"
    for plat in commande["Commande"].values():
        if plat["Statut"] == "En attente":
            plat["Statut"] = "En préparation"

    # TODO : Mettre en place un système d'impression de ticket de commande
    # 1 ticket par plat mis en préparation avec l'ID complet, le nom du plat et la composition
    # 1 ticket récapitulatif avec l'ID de la commande, le montant total, le type de paiement et la date de validation, la liste des plats mis en préparation (numéro de plat et nom du plat)

    # Sauvegarder les modifications
    with open(chemin_fichier, "w", encoding="utf-8") as fichier:
        json.dump(commande, fichier, indent=4, ensure_ascii=False)

    # Déplacer le fichier
    dossier_en_cours = os.path.join(os.path.dirname(chemin_fichier), "en_cours")
    os.makedirs(dossier_en_cours, exist_ok=True)
    os.rename(chemin_fichier, os.path.join(dossier_en_cours, os.path.basename(chemin_fichier)))

    # Rafraîchir l'affichage
    affichage_commande_actuelle()
    affichage_commandes_validées()

def plat_prêt(chemin_fichier, plat_id_complet, affichage_commandes_validées):
    """
    Change le statut d'un plat de "En préparation" à "Prêt" et rafraîchit l'affichage.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    :param plat_id_complet: Identifiant complet du plat (aaaammjj-000-00).
    :param affichage_commandes_validées: Fonction pour rafraîchir l'affichage des commandes validées.
    """
    commande_data = charger_fichier_json(chemin_fichier)
    if not commande_data:
        return

    # Extraire le numéro de plat (ex. #00) à partir de l'ID complet
    numero_plat = f"#{plat_id_complet.split('-')[-1]}"

    # Vérifier si le plat existe et est en préparation
    if numero_plat in commande_data["Commande"] and commande_data["Commande"][numero_plat]["Statut"] == "En préparation":
        # Mettre à jour le statut du plat
        commande_data["Commande"][numero_plat]["Statut"] = "Prêt"

        # Remplir la date et l'heure de mise en livraison
        commande_data["Commande"][numero_plat]["Date de mise en livraison"] = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]

        # TODO: Intégrer un système d'envoi de SMS pour prévenir que le plat est prêt
        # Exemple : envoyer_sms(commande_data["Informations"]["Contact"], f"Votre plat {commande_data['Commande'][numero_plat]['Nom']} est prêt !")

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande_data, fichier, indent=4, ensure_ascii=False)

        # Rafraîchir l'affichage
        affichage_commandes_validées()

def livrer_plat(chemin_fichier, plat_id_complet, affichage_commandes_validées):
    """
    Change le statut d'un plat de "Prêt" à "Livré", remplit la date de livraison,
    exécute la commande terminer_commande et rafraîchit l'affichage.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    :param plat_id_complet: Identifiant complet du plat (aaaammjj-000-00).
    :param affichage_commandes_validées: Fonction pour rafraîchir l'affichage des commandes validées.
    """
    commande_data = charger_fichier_json(chemin_fichier)
    if not commande_data:
        return

    # Extraire le numéro de plat (ex. #00) à partir de l'ID complet
    numero_plat = f"#{plat_id_complet.split('-')[-1]}"

    # Vérifier si le plat existe et est prêt
    if numero_plat in commande_data["Commande"] and commande_data["Commande"][numero_plat]["Statut"] == "Prêt":
        # Mettre à jour le statut du plat
        commande_data["Commande"][numero_plat]["Statut"] = "Livré"

        # Remplir la date et l'heure de livraison
        commande_data["Commande"][numero_plat]["Date de livraison"] = [datetime.now().strftime("%d/%m/%Y"), datetime.now().strftime("%H:%M")]

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande_data, fichier, indent=4, ensure_ascii=False)

        # Exécuter la commande terminer_commande
        terminer_commande(chemin_fichier)

        # Rafraîchir l'affichage
        affichage_commandes_validées()

def terminer_commande(chemin_fichier):
    """
    Termine une commande si tous les plats (hors annulés) sont livrés.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    """
    commande = charger_fichier_json(chemin_fichier)
    if not commande:
        return

    # Vérifier si tous les plats (hors annulés) sont livrés
    plats = commande["Commande"].values()
    if all(plat["Statut"] in ["Livré", "Annulé"] for plat in plats):
        # Modifier le statut de la commande
        commande["Informations"]["Statut"] = "Terminée"

        # Trouver la date et l'heure de livraison du dernier plat livré
        dernier_livraison = max(
            (plat["Date de livraison"] for plat in plats if plat["Statut"] == "Livré"),
            default=["", ""]
        )
        commande["Informations"]["Date de livraison"] = dernier_livraison

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

        # Déplacer le fichier dans le dossier "terminee"
        dossier_terminee = os.path.join(
            os.path.dirname(os.path.dirname(chemin_fichier)), "terminee"
        )
        os.makedirs(dossier_terminee, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_terminee, os.path.basename(chemin_fichier)))

# == Annulation de commande == #
def annuler_commande(chemin_fichier):
    commande = charger_fichier_json(chemin_fichier)
    if not commande:
        return

    # Vérifier si tous les plats sont annulés
    plats = commande["Commande"].values()
    if all(plat["Statut"] == "Annulé" for plat in plats):
        commande["Informations"]["Statut"] = "Annulée"

        # Sauvegarder les modifications
        with open(chemin_fichier, "w", encoding="utf-8") as fichier:
            json.dump(commande, fichier, indent=4, ensure_ascii=False)

        # Déplacer le fichier
        dossier_annulee = os.path.join(os.path.dirname(chemin_fichier), "annulee")
        os.makedirs(dossier_annulee, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_annulee, os.path.basename(chemin_fichier)))

def annuler_plat(commande_file, plat_id, chemin_fichier, affichage_commande_actuelle):
    """
    Annule un plat dans la commande en cours.
    """
    commande_data = charger_fichier_json(commande_file)
    if not commande_data:
        return

    # Mettre à jour le statut du plat
    commande_data["Commande"][plat_id]["Statut"] = "Annulé"

    # Recalculer le montant total
    commande_data["Informations"]["Montant"] = sum(
        plat["Prix"] for plat in commande_data["Commande"].values() if plat["Statut"] != "Annulé"
    )
    
    # Sauvegarder les modifications
    with open(commande_file, "w", encoding="utf-8") as f:
        json.dump(commande_data, f, indent=4, ensure_ascii=False)

    # Vérifier si tous les plats sont annulés
    annuler_commande(chemin_fichier)

    # Rafraîchir l'affichage
    affichage_commande_actuelle()

# == Modification de commande == #
def modifier_plat(plat):
    """
    Ouvre la fenêtre de personnalisation pour modifier un plat existant.
    """
    from front_temp import travaux_en_cours
    travaux_en_cours()