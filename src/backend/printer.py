#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
printer.py

Description:
    Impression des tickets de commande récapitulatif et de cuisine après validation d'une commande.

Author :
    Dracudar

Version:
    2.0

Date de création :
    2025.06.04

Date de modification:
    2026.06.07
"""

import os
from PIL import Image
from escpos.printer import Usb
from src.backend.commandes_utils import charger_fichier_commande
from src.backend.app_config import get_printer_config, get_print_options


def charger_logo(nom_image, taille=()):
    """
    Charge et redimensionne une image PIL pour l'impression thermique.
    :param nom_image: Nom du fichier image (ex. "image.png").
    :param taille: Tuple (largeur, hauteur) pour redimensionner l'image.
    :return: PIL.Image.Image
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    chemin = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'imgs', nom_image))
    try:
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


def _get_printer():
    """Instancie l'imprimante USB depuis la configuration."""
    cfg = get_printer_config()
    return Usb(cfg["vendor_id"], cfg["product_id"], cfg["interface"], profile=cfg["modele"])


def print_ticket_recap(chemin_fichier):
    """Imprime un ticket récapitulatif de la commande (si activé dans la config)."""
    if not get_print_options()["ticket_client"]:
        return
    try:
        p = _get_printer()

        commande = charger_fichier_commande(chemin_fichier)
        infos = commande["Informations"]
        plats = commande["Commande"]

        # Logo centré — 576px = largeur imprimable TM-T20II (80mm à 203 DPI)
        logo = charger_logo("En-tete ticket V1.png", taille=(576, 123))
        p.image(logo)

        p.set(align='center', width=2, height=2)
        p.text(f"Date : {infos['Date de création'][0]} \n")
        p.set(width=8, height=8)
        p.text(f"{str(infos['ID'])[-3:]}\n")
        p.set(align='left', width=1, height=1)
        p.text(f"Montant : {infos['Montant']} €\n")
        p.text(f"Type de paiement : {infos['Type de paiement']}\n")

        for plat_id, plat in plats.items():
            if plat["Statut"] == "En attente":
                p.text("-" * 48 + "\n")
                if plat["Plat"] == "Frites":
                    p.text(f"{plat_id} - {plat['Nom']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")

                elif plat["Plat"] == "Grillade":
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")

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
                    if plat['Composition']['Accompagnement'] == "Sans":
                        p.text("Sans accompagnement\n")
                    else:
                        p.text(f"Accompagnement : {plat['Composition']['Accompagnement']}\n")

                elif plat["Plat"] == "Pizza":
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"{plat['Recette']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")
                    p.text('\n')
                    p.text(f"Base : {plat['Composition']['Base']}\n")
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']['Ingrédients']:
                        p.text(f"  - {ingredient}\n")

                elif plat["Plat"] == "Fish & Chips":
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")

                elif plat["Plat"] == "Salade composée":
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")
                    p.text('\n')
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']['Ingrédients']:
                        p.text(f"  - {ingredient}\n")

                elif plat["Plat"] == "Crêpe":
                    p.text(f"{plat_id} - {plat['Nom']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")

                elif plat["Plat"] == "Pizza dessert":
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")
                    p.text('\n')
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']:
                        p.text(f"  - {ingredient}\n")

                else:
                    p.text(f"{plat_id} - {plat['Plat']}\n")
                    p.text(f"Prix : {plat['Prix']} €\n")

        p.cut()
        p.close()

    except Exception as e:
        print(f"Imprimante non disponible : {e}")


def print_ticket_cuisine(chemin_fichier):
    """Imprime un ticket de cuisine par plat (si activé dans la config)."""
    if not get_print_options()["ticket_cuisine"]:
        return
    try:
        p = _get_printer()

        commande = charger_fichier_commande(chemin_fichier)
        infos = commande["Informations"]
        plats = commande["Commande"]

        for plat_id, plat in plats.items():
            if plat["Statut"] == "En attente":

                id_parts = str(plat['ID']).split('-')
                if len(id_parts) >= 3:
                    id_affiche = f"{id_parts[1]}-{id_parts[2]}"
                else:
                    id_affiche = str(plat['ID'])

                p.set(align='center', width=2, height=2)
                p.text(f"Date : {infos['Date de création'][0]} \n")
                p.set(width=8, height=8)
                p.text(f"{id_affiche}\n")
                p.set(align='left', width=1, height=1)

                if plat["Plat"] == "Frites":
                    p.text(f"{plat['Nom']}\n")
                    p.text("\n" * 5)

                elif plat["Plat"] == "Grillade":
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
                    if plat['Composition']['Accompagnement'] == "Sans":
                        p.text("Sans accompagnement\n")
                    else:
                        p.text(f"Accompagnement : {plat['Composition']['Accompagnement']}\n")

                elif plat["Plat"] == "Pizza":
                    p.text(f"{plat['Plat']}\n")
                    p.text(f"{plat['Recette']}\n")
                    p.text("\n")
                    p.text(f"Base : {plat['Composition']['Base']}\n")
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']['Ingrédients']:
                        p.text(f"  - {ingredient}\n")

                elif plat["Plat"] == "Fish & Chips":
                    p.text(f"{plat['Plat']}\n")
                    p.text("\n")
                    p.text("Composition :\n")
                    p.text("  - Poisson pané\n")
                    p.text("  - Portion de frites\n")

                elif plat["Plat"] == "Salade composée":
                    p.text(f"{plat['Plat']}\n")
                    p.text("\n")
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']['Ingrédients']:
                        p.text(f"  - {ingredient}\n")

                elif plat["Plat"] == "Crêpe":
                    p.text(f"{plat['Nom']}\n")
                    p.text("\n" * 3)

                elif plat["Plat"] == "Pizza dessert":
                    p.text(f"{plat['Plat']}\n")
                    p.text("\n")
                    p.text("Composition :\n")
                    for ingredient in plat['Composition']:
                        p.text(f"  - {ingredient}\n")

                else:
                    p.text(f"{plat['Plat']}\n")

                p.text("\n")
                p.cut()

        p.close()

    except Exception as e:
        print(f"Imprimante non disponible : {e}")
