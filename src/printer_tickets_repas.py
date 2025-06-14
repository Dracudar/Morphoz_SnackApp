'''
Script pour imprimer des tickets de repas gratuits à partir d'un fichier Excel.
'''

import os
from PIL import Image
from escpos.printer import Usb
import pandas as pd
from datetime import datetime, timedelta

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


def imprimer_ticket(p, logo, nom, cat,  date_début, date_fin):
    p.set(align='center')
    p.image(logo)
    p.text("\n")
    p.set(width=8, height=8)
    p.text("TICKET REPAS GRATUIT\n")
    p.text("\n")
    p.text(f"{nom} ({cat})\n")
    p.text("\n")
    p.set(bold=True)
    p.text(f"Valable du {date_début} au {date_fin}\n")
    p.set(bold=False)
    p.text("\n" * 5)
    p.cut()

def ticket_repas_gratuit():
    p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE)

    logo = charger_logo("En-tete ticket V1.png", taille=(500, 107))  # Respecte le ratio 7:1.5

    # Informations
    date_début = "20/06/2025"
    date_fin = "21/06/2025"
    fichier_liste = "tickets_repas_MS09.xlsx"

    # Lecture du fichier Excel
    chemin = os.path.abspath(os.path.join(BASE_DIR, '..', 'assets', fichier_liste))
    df = pd.read_excel(chemin)

    # Vérification des colonnes nécessaires
    colonnes_requises = ["Nom", "Catégorie", "Quantité"]
    for col in colonnes_requises:
        if col not in df.columns:
            raise ValueError(f"La colonne '{col}' est manquante dans le fichier Excel.")

    # Génération de la liste des jours de l'événement
    d1 = datetime.strptime(date_début, "%d/%m/%Y")
    d2 = datetime.strptime(date_fin, "%d/%m/%Y")
    nb_jours = (d2 - d1).days + 1
    jours = [(d1 + timedelta(days=i)).strftime("%d/%m/%Y") for i in range(nb_jours)]
    print(f"Jours de l'événement : {jours}")

    print("Génération des tickets de repas...")
    for index, row in df.iterrows():
        nom = row["Nom"]
        cat = str(row["Catégorie"]).strip().lower()
        qtt = int(row["Quantité"])

        if cat.startswith("artiste"):
            for i, date in enumerate(jours):
                # Premier jour : 1 repas, autres jours : 2 repas
                nb_repas = 1 if i == 0 else 2
                for _ in range(nb_repas * qtt):
                    imprimer_ticket(p, logo, nom, row["Catégorie"], date_début, date_fin)
        elif cat.startswith("bénévole"):
            for date in jours:
                imprimer_ticket(p, logo, nom, row["Catégorie"], date_début, date_fin)
        else:
            print(f"Catégorie inconnue pour {nom} : {row['Catégorie']}")

    print("Tickets de repas générés avec succès.")
    p.close()  # Fermer la connexion à l'imprimante
    print("Imprimante déconnectée.")

ticket_repas_gratuit()
