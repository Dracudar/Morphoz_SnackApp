'''
Gestion des images et icônes pour l'interface tkinter.
'''

import os
from PIL import Image, ImageTk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Répertoire du fichier

# === Chargement et redimensionnement d'images === #
def charger_img(nom_image, taille=()):
    """
    Charge et redimensionne une image pour tkinter depuis le dossier assets/img.

    :param nom_image: Nom du fichier image (ex. "image.png").
    :param taille: Tuple (largeur, hauteur) pour redimensionner l'image.
    :return: ImageTk.PhotoImage pour utilisation dans tkinter.
    """
    chemin = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'img', nom_image))
    try:
        img = Image.open(chemin)
        img = img.resize(taille, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except FileNotFoundError:
        raise FileNotFoundError(f"L'image '{nom_image}' est introuvable dans 'assets/img'.")
    except Exception as e:
        raise RuntimeError(f"Une erreur est survenue lors du chargement de l'image '{nom_image}': {e}")
