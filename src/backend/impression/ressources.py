#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ressources.py

Description:
    Chargement des images (logo) utilisées dans les tickets d'impression
    thermique, avec conversion PNG/SVG vers le mode 1-bit attendu par
    l'imprimante.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.16

Date de modification:
    2026.06.16
"""

import io
import os
from PIL import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM


def charger_logo(nom_image, taille=()):
    """
    Charge et redimensionne une image PIL pour l'impression thermique.
    Accepte les formats PNG et SVG.
    :param nom_image: Nom du fichier image (ex. "image.png" ou "image.svg").
    :param taille: Tuple (largeur, hauteur) pour redimensionner l'image.
    :return: PIL.Image.Image en mode 1-bit pour l'imprimante thermique
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    chemin = os.path.abspath(os.path.join(BASE_DIR, '..', '..', '..', 'assets', 'imgs', nom_image))
    try:
        if nom_image.lower().endswith('.svg'):
            drawing = svg2rlg(chemin)
            if taille:
                sx, sy = taille[0] / drawing.width, taille[1] / drawing.height
                drawing.width, drawing.height = taille[0], taille[1]
                drawing.transform = (sx, 0, 0, sy, 0, 0)
            png_bytes = renderPM.drawToString(drawing, fmt="PNG")
            img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        else:
            img = Image.open(chemin).convert("RGBA")
            if taille:
                img = img.resize(taille, Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
        img = img.convert("L")
        img = img.point(lambda x: 0 if x < 128 else 255, "1")
        return img
    except FileNotFoundError:
        raise FileNotFoundError(f"L'image '{nom_image}' est introuvable dans 'assets/imgs'.")
    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement de l'image '{nom_image}': {e}")
