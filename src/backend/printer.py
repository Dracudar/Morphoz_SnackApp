'''

'''

import json
import os
from PIL import Image
from escpos.printer import Usb
from .commandes_utils import charger_fichier_commande

# Paramètres de configuration de l'imprimante thermique
IMPRIMANTE_USB_VENDOR_ID = 0x04B8
IMPRIMANTE_USB_PRODUCT_ID = 0x0E15
IMPRIMANTE_USB_INTERFACE = 0

# Fonction pour charger une image et la redimensionner pour l'impression thermique
def charger_logo(nom_image, taille=()):
    """
    Charge et redimensionne une image PIL pour l'impression thermique.
    :param nom_image: Nom du fichier image (ex. "image.png").
    :param taille: Tuple (largeur, hauteur) pour redimensionner l'image.
    :return: PIL.Image.Image
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Répertoire du fichier
    chemin = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'img', nom_image))
    try:
        img = Image.open(chemin).convert("RGBA")
        if taille:
            img = img.resize(taille, Image.Resampling.LANCZOS)
        # Remplacer la transparence par du blanc
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
        img = img.convert("L")  # Niveaux de gris
        img = img.point(lambda x: 0 if x < 128 else 255, "1")  # Seuillage manuel
        return img
    except FileNotFoundError:
        raise FileNotFoundError(f"L'image '{nom_image}' est introuvable dans 'assets/img'.")
    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement de l'image '{nom_image}': {e}")

def print_ticket_recap(chemin_fichier):
    """Imprime un ticket récapitulatif de la commande."""
    # Charger l'imprimante USB
    try:
        p = Usb(IMPRIMANTE_USB_VENDOR_ID, IMPRIMANTE_USB_PRODUCT_ID, IMPRIMANTE_USB_INTERFACE)

        # Charger la commande depuis le fichier JSON
        commande = charger_fichier_commande(chemin_fichier)
        infos = commande["Informations"]
        plats = commande["Commande"]

        # En-tête
        logo = charger_logo("En-tete ticket V1.png", taille=(500, 107))  # Respecte le ratio 7:1.5
        p.set(align='center')
        p.image(logo)
        p.set(align='left')
        # Informations de la commande
        p.set(align='center', width=2, height=2)
        p.text(f"Date : {infos['Date de création'][0]} \n")  # Affiche la date de création (sans l'heure)
        p.set(width=8, height=8)
        p.text(f"{str(infos['ID'])[-3:]}\n")  # Affiche les 3 derniers chiffres de l'ID
        p.set(align='left', width=1, height=1)
        p.text(f"Montant : {infos['Montant']} €\n")  # Affiche le montant total avec la devise
        p.text(f"Type de paiement : {infos['Type de paiement']}\n")

        # Parcours des plats de la commande
        for plat_id, plat in plats.items():
            if plat["Statut"] == "En attente":  # Imprime uniquement les plats en attente
                p.text("-" * 48 + "\n")  # Ligne de séparation
                # Personnalisation selon le type de plat
                if plat["Plat"] == "Frites" :
                    p.text(f"{plat_id} - {plat['Nom']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")  # Affiche le prix du plat

                elif plat["Plat"] == "Grillade" :
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")  # Affiche le prix du plat

                    if isinstance(plat['Composition']['Viandes'], dict):
                        if len(plat['Composition']['Viandes']) == 1:
                            nom_viande, quantite = next(iter(plat['Composition']['Viandes'].items()))
                            if quantite > 1:
                                p.text(f"Viandes : {nom_viande} x{quantite}\n")
                            else:
                                p.text(f"Viandes : {nom_viande}\n")
                        elif len(plat['Composition']['Viandes']) > 1:
                            p.text("Viandes :\n")
                            for nom_viande, quantite in plat['Composition']['Viandes'].items():
                                if quantite > 1:
                                    p.text(f"  - {nom_viande} x{quantite}\n")
                                else:
                                    p.text(f"  - {nom_viande}\n")
                    if plat['Composition']['Accompagnement'] == "Sans" :
                        p.text("Sans accompagnement\n")
                    else:    
                        p.text(f"Accompagnement : {plat['Composition']['Accompagnement']}\n")

                elif plat["Plat"] == "Pizza" :
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    # p.text(f"{plat['Recette']}\n")  # TODO : voir pour enregistrer la recette de pizza choisie dans le fichier de commande
                    p.text(f"Prix : {plat['Prix']} €\n")  # Affiche le prix du plat
                    p.text('\n')
                    p.text(f"Base : {plat['Composition']['Base']}\n")
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']['Ingrédients']:
                        p.text(f"  - {ingredient}\n")
                
                elif plat["Plat"] == "Fish & Chips" :
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")  # Affiche le prix du plat

                elif plat["Plat"] == "Salade composée" :
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")  # Affiche le prix du plat
                    p.text('\n')
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']['Ingrédients']:
                        p.text(f"  - {ingredient}\n")

                elif plat["Plat"] == "Pizza dessert" :
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")  # Affiche le prix du plat
                    p.text('\n')
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']:
                        p.text(f"  - {ingredient}\n")
                
                else:
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")  # Affiche le prix du plat

        p.cut()
        p.close()
        
    except Exception as e:
        print(f"Imprimante non disponible : {e}")
        return  # Arrête la fonction si l'imprimante n'est pas dispo

def print_ticket_cuisine(chemin_fichier):
    """Imprime un ticket personnalisé pour chaque plat de la commande."""
    
    # Charger l'imprimante USB
    try:
        p = Usb(IMPRIMANTE_USB_VENDOR_ID, IMPRIMANTE_USB_PRODUCT_ID, IMPRIMANTE_USB_INTERFACE)

        # Charger la commande depuis le fichier JSON    
        commande = charger_fichier_commande(chemin_fichier)
        infos = commande["Informations"]
        plats = commande["Commande"]

        # Parcours des plats de la commande
        for plat_id, plat in plats.items():
            if plat["Statut"] == "En attente":  # Imprime uniquement les plats en attente

                # Extraction de l'ID plat pour l'affichage
                id_parts = str(plat['ID']).split('-')
                if len(id_parts) >= 3:
                    id_affiche = f"{id_parts[1]}-{id_parts[2]}"
                else:
                    id_affiche = str(plat['ID'])  # fallback si le format ne correspond pas

                # En-tête du ticket cuisine (date et ID plat 000-00)
                p.set(align='center', width=2, height=2)
                p.text(f"Date : {infos['Date de création'][0]} \n")  # Affiche la date de création (sans l'heure)
                p.set(width=8, height=8)
                p.text(f"{id_affiche}\n")  # Affiche le 000-00
                p.set(align='left', width=1, height=1)

                # Personnalisation selon le type de plat
                if plat["Plat"] == "Frites" :
                    p.text(f"{plat['Nom']}\n")
                    p.text("\n" * 5)  # Ligne vide

                elif plat["Plat"] == "Grillade" :
                    p.text(f"{plat['Plat']}\n")

                    if isinstance(plat['Composition']['Viandes'], dict):
                        if len(plat['Composition']['Viandes']) == 1:
                            nom_viande, quantite = next(iter(plat['Composition']['Viandes'].items()))
                            if quantite > 1:
                                p.text(f"Viandes : {nom_viande} x{quantite}\n")
                            else:
                                p.text(f"Viandes : {nom_viande}\n")
                        elif len(plat['Composition']['Viandes']) > 1:
                            p.text("Viandes :\n")
                            for nom_viande, quantite in plat['Composition']['Viandes'].items():
                                if quantite > 1:
                                    p.text(f"  - {nom_viande} x{quantite}\n")
                                else:
                                    p.text(f"  - {nom_viande}\n")
                    if plat['Composition']['Accompagnement'] == "Sans" :
                        p.text("Sans accompagnement\n")
                    else:    
                        p.text(f"Accompagnement : {plat['Composition']['Accompagnement']}\n")

                elif plat["Plat"] == "Pizza" :
                    p.text(f"{plat['Plat']}\n")
                    # p.text(f"{plat['Recette']}\n")  # TODO : voir pour enregistrer la recette de pizza choisie dans le fichier de commande
                    p.text("\n") # Ligne vide
                    p.text(f"Base : {plat['Composition']['Base']}\n")
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']['Ingrédients']:
                        p.text(f"  - {ingredient}\n")
                
                elif plat["Plat"] == "Fish & Chips" :
                    p.text(f"{plat['Plat']}\n")
                    p.text("\n") # Ligne vide
                    p.text("Composition :\n")
                    p.text("  - Poisson pané\n")
                    p.text("  - Portion de frites\n")

                elif plat["Plat"] == "Salade composée" :
                    p.text(f"{plat['Plat']}\n")
                    p.text("\n") # Ligne vide
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']['Ingrédients']:
                        p.text(f"  - {ingredient}\n")

                elif plat["Plat"] == "Pizza dessert" :
                    p.text(f"{plat['Plat']}\n")
                    p.text("\n") # Ligne vide
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']:
                        p.text(f"  - {ingredient}\n")
                
                else:
                    p.text(f"{plat['Plat']}\n")

                p.text("\n") # Ligne vide
                p.cut()
                p.close()

    except Exception as e:
        print(f"Imprimante non disponible : {e}")
        return  # Arrête la fonction si l'imprimante n'est pas disponible
