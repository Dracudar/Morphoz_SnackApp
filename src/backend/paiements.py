"""
Fonctionnalité pour mettre à jour le champ relatif au type de paiement dans le fichier de commande.
Permet de lancer la validation de la commande après paiement et d'imprimer les tickets.
"""

import json  # Pour manipuler les données JSON
from .commandes_utils import charger_fichier_commande  # Pour charger le fichier de commande JSON
from .commandes_saisie_gestion import valider_commande  # Pour valider la commande après paiement et imprimer les tickets

    
def paiement_carte(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
        commande = charger_fichier_commande(chemin_fichier)
        commande["Informations"]["Type de paiement"] = "Carte"  # Met à jour le type de paiement dans la commande
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande, f, indent=4, ensure_ascii=False)

        valider_commande(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées)

def paiement_especes(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
        commande = charger_fichier_commande(chemin_fichier)
        commande["Informations"]["Type de paiement"] = "Espèces"  # Met à jour le type de paiement dans la commande
        with open(chemin_fichier, "w", encoding="utf-8") as f:
            json.dump(commande, f, indent=4, ensure_ascii=False)

        valider_commande(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées)


def gratuit(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
    commande = charger_fichier_commande(chemin_fichier)
    commande["Informations"]["Type de paiement"] = "Repas gratuit"  # Met à jour le type de paiement dans la commande
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(commande, f, indent=4, ensure_ascii=False)

    valider_commande(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées)