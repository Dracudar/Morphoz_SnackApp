'''
Script pour imprimer des tickets de repas gratuits à partir d'un fichier Excel.
'''

import os
from PIL import Image
from escpos.printer import Usb
import pandas as pd

from config_printer import (
    IMPRIMANTE_USB_VENDOR_ID as VENDOR_ID, 
    IMPRIMANTE_USB_PRODUCT_ID as PRODUCT_ID, 
    IMPRIMANTE_USB_INTERFACE as INTERFACE
)  # Import des paramètres de configuration de l'imprimante thermique

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Répertoire du fichier

# Fonction pour le chargement de l'image d'en-tête et son redimensionnement
def charger_logo(nom_image, taille=()):
    """
    Charge et redimensionne une image PIL pour l'impression thermique.
    :param nom_image: Nom du fichier image (ex. "image.png").
    :param taille: Tuple (largeur, hauteur) pour redimensionner l'image.
    :return: PIL.Image.Image
    """
    chemin = os.path.abspath(os.path.join(BASE_DIR, '..', 'assets', 'img', nom_image))
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


def ticket_repas_gratuit():
    p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE)

    logo = charger_logo("En-tete ticket V1.png", taille=(500, 107))  # Respecte le ratio 7:1.5

    # Lecture du fichier Excel
    nom_fichier = "ticket_repas_MS09.xlsx"
    chemin = os.path.abspath(os.path.join(BASE_DIR, '..', 'assets', nom_fichier))
    df = pd.read_excel(chemin)

    # Génération des tickets
    for index, row in df.iterrows():
        nom = row["Nom"]
        cat = row["Catégorie"]
        for date in ["20/06/2025", "21/06/2025"]:
            nb_tickets = row[date]
            if pd.notna(nb_tickets) and int(nb_tickets) > 0:
                for _ in range(int(nb_tickets)):

                    # Construction du ticket
                    p.set(align='center')
                    p.image(logo)
                    p.text("\n")
                    p.set(width=8, height=8)
                    p.text("TICKET REPAS GRATUIT\n")
                    p.text("\n")
                    p.text(f"{nom} ({cat})\n")
                    p.text("\n")
                    p.text("Valable le ")
                    p.set(bold=True)
                    p.text(date)
                    p.set(bold=False)
                    p.text("\n" * 5)  # Ajoute des lignes vides en fin de ticket
            
                    p.cut()  # Couper le papier

ticket_repas_gratuit()
