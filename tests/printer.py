'''

'''

import os
from PIL import Image
from escpos.printer import Usb

def charger_logo(nom_image, taille=()):
    """
    Charge et redimensionne une image PIL pour l'impression thermique.
    :param nom_image: Nom du fichier image (ex. "image.png").
    :param taille: Tuple (largeur, hauteur) pour redimensionner l'image.
    :return: PIL.Image.Image
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Répertoire du fichier
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


def imprimer_entete(p):
    logo = charger_logo("MegaSouye.png", taille=(150, 150))
    # Centrer et imprimer le logo
    p.set(align='center')
    p.image(logo)
    # Imprimer le nom en gras, centré, à côté du logo (sur la ligne en dessous)
    p.set(bold=True, align='center', width=8, height=8)
    p.text("MegaSnack\n")
    p.set(bold=False, align='left', width=1, height=1)


def imprimer_test():
    p = Usb(0x04B8, 0x0E15, 0)

    imprimer_entete(p)
    p.text("\n")
    p.set(align='center', width=3, height=3)
    p.text("jj/mm/aaaa\n")
    p.set(align='left', width=1, height=1)
    p.set(align='center', width=5, height=5)
    p.text("\n")
    p.text("000-00\n")
    p.set(align='left', width=3, height=3)
    p.text("\n")
    p.text("Nom du plat\n")
    p.text("Composition du plat\n")
    p.text("\n")
    p.text("\n")

    # Couper le papier
    p.cut()

imprimer_test()

#=== Sandbox ===#
"""
p = Usb(0x04B8, 0x0E15, 0)
logo = charger_logo("MegaSouye.png", taille=(500, 500))
# Centrer et imprimer le logo
p.set(align='center')
p.image(logo)
p.text("\n")
p.text("\n")
p.cut()
"""