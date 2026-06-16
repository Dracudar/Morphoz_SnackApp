#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
printer.py

Description:
    Impression des tickets de commande récapitulatif et de cuisine après validation d'une commande.
    Fournit également des fonctions de réimpression manuelle indépendantes des options
    d'impression automatique.

Author :
    Dracudar

Version:
    2.3

Date de création :
    2025.06.04

Date de modification:
    2026.06.14
"""

import io
import os
from PIL import Image
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from escpos.printer import Usb
from src.backend.commandes.stock_utils import charger_fichier_commande
from src.backend.config.imprimante import get_printer_config
from src.backend.config.impression import get_print_options
from src.backend import logger


def charger_logo(nom_image, taille=()):
    """
    Charge et redimensionne une image PIL pour l'impression thermique.
    Accepte les formats PNG et SVG.
    :param nom_image: Nom du fichier image (ex. "image.png" ou "image.svg").
    :param taille: Tuple (largeur, hauteur) pour redimensionner l'image.
    :return: PIL.Image.Image en mode 1-bit pour l'imprimante thermique
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    chemin = os.path.abspath(os.path.join(BASE_DIR, '..', '..', 'assets', 'imgs', nom_image))
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


def _get_printer():
    """Instancie l'imprimante USB depuis la configuration."""
    cfg = get_printer_config()
    return Usb(cfg["vendor_id"], cfg["product_id"], cfg["interface"], profile=cfg["modele"])


# ── Helpers internes ──────────────────────────────────────────────────────────

def _do_print_recap(commande: dict, p, reprint: bool = False) -> None:
    """Imprime sur p le ticket récapitulatif complet d'une commande (avec coupure finale).

    Si reprint=True, imprime tous les plats quelle que soit leur statut.
    """
    infos = commande["Informations"]
    plats = commande["Commande"]

    logo = charger_logo("MegaSnack.svg", taille=(576, 123))
    p.image(logo)

    p.set(align='center', width=2, height=2)
    p.text(f"Date : {infos['Date de création'][0]} \n")
    p.set(width=8, height=8)
    p.text(f"{str(infos['ID'])[-3:]}\n")
    p.set(align='left', width=1, height=1)
    p.text(f"Montant : {infos['Montant']} €\n")
    p.text(f"Type de paiement : {infos['Type de paiement']}\n")

    for plat_id, plat in plats.items():
        if reprint or plat["Statut"] == "En attente":
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


def _print_plat_ticket(plat: dict, infos: dict, p) -> None:
    """Imprime sur p un ticket cuisine complet pour un seul plat (avec coupure finale)."""
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


# ── Impression automatique (à la validation de commande) ─────────────────────

def print_ticket_recap(chemin_fichier):
    """Imprime un ticket récapitulatif de la commande (si activé dans la config)."""
    options = get_print_options()
    if not options["impression_active"] or not options["ticket_client"]:
        return
    try:
        p = _get_printer()
        commande = charger_fichier_commande(chemin_fichier)
        _do_print_recap(commande, p)
        p.close()
        logger.log(logger.IMPRESSION_TICKET, {
            "type": "recap",
            "id_commande": commande["Informations"]["ID"],
            "contexte": "auto",
        })
    except Exception as e:
        logger.log(logger.ERREUR, {
            "contexte": "impression_recap_auto",
            "id_commande": chemin_fichier,
            "detail": str(e),
        })


def print_ticket_cuisine(chemin_fichier):
    """Imprime un ticket de cuisine par plat (si activé dans la config)."""
    options = get_print_options()
    if not options["impression_active"] or not options["ticket_cuisine"]:
        return
    try:
        p = _get_printer()
        commande = charger_fichier_commande(chemin_fichier)
        infos = commande["Informations"]
        plats = commande["Commande"]

        nb_tickets = 0
        for plat_id, plat in plats.items():
            if plat["Statut"] == "En attente":
                _print_plat_ticket(plat, infos, p)
                nb_tickets += 1

        p.close()
        logger.log(logger.IMPRESSION_TICKET, {
            "type": "cuisine",
            "id_commande": infos["ID"],
            "nb_tickets": nb_tickets,
            "contexte": "auto",
        })
    except Exception as e:
        logger.log(logger.ERREUR, {
            "contexte": "impression_cuisine_auto",
            "id_commande": chemin_fichier,
            "detail": str(e),
        })


# ── Réimpression manuelle (depuis l'historique) ───────────────────────────────

def reprint_ticket_recap(chemin_fichier: str) -> None:
    """Réimprime le ticket récapitulatif sans vérifier les options d'impression automatique.

    Lève RuntimeError si l'impression échoue.
    """
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        raise ValueError("Fichier commande introuvable")
    try:
        p = _get_printer()
        _do_print_recap(commande, p, reprint=True)
        p.close()
        logger.log(logger.IMPRESSION_TICKET, {
            "type": "recap",
            "id_commande": commande["Informations"]["ID"],
            "contexte": "reimpression",
        })
    except Exception as e:
        logger.log(logger.ERREUR, {
            "contexte": "reimpression_recap",
            "id_commande": commande["Informations"]["ID"],
            "detail": str(e),
        })
        raise RuntimeError(f"Erreur d'impression : {e}") from e


def reprint_ticket_cuisine_plat(chemin_fichier: str, plat_id: str) -> None:
    """Réimprime le ticket cuisine d'un plat spécifique sans vérifier les options d'impression automatique.

    :param plat_id: Identifiant complet du plat (ex. 20260610-001-G001).
    Lève RuntimeError si l'impression échoue.
    """
    commande = charger_fichier_commande(chemin_fichier)
    if not commande:
        raise ValueError("Fichier commande introuvable")
    plat = next((v for v in commande["Commande"].values() if v.get("ID") == plat_id), None)
    if plat is None:
        raise ValueError(f"Plat {plat_id} introuvable dans la commande")
    try:
        p = _get_printer()
        _print_plat_ticket(plat, commande["Informations"], p)
        p.close()
        logger.log(logger.IMPRESSION_TICKET, {
            "type": "cuisine",
            "id_commande": commande["Informations"]["ID"],
            "id_plat": plat_id,
            "contexte": "reimpression",
        })
    except Exception as e:
        logger.log(logger.ERREUR, {
            "contexte": "reimpression_cuisine_plat",
            "id_commande": commande["Informations"]["ID"],
            "id_plat": plat_id,
            "detail": str(e),
        })
        raise RuntimeError(f"Erreur d'impression : {e}") from e


def reprint_all_active_cuisine() -> int:
    """Réimprime les tickets cuisine de tous les plats en préparation ou prêts dans les commandes actives.

    Retourne le nombre de tickets imprimés.
    Lève RuntimeError si l'impression échoue.
    """
    from src.backend.data.prep import get_live_orders_prep

    plats_actifs = [
        plat for plat in get_live_orders_prep()
        if plat["status"].lower() in ("en préparation", "prêt")
    ]
    if not plats_actifs:
        return 0

    try:
        p = _get_printer()
        count = 0
        for plat_item in plats_actifs:
            commande = charger_fichier_commande(str(plat_item["file"]))
            if not commande:
                continue
            plat = next(
                (v for v in commande["Commande"].values() if v.get("ID") == plat_item["id"]),
                None,
            )
            if plat is None:
                continue
            _print_plat_ticket(plat, commande["Informations"], p)
            count += 1
        p.close()
        logger.log(logger.IMPRESSION_TICKET, {
            "type": "cuisine",
            "nb_tickets": count,
            "contexte": "reimpression_globale",
        })
        return count
    except Exception as e:
        logger.log(logger.ERREUR, {
            "contexte": "reimpression_cuisine_globale",
            "detail": str(e),
        })
        raise RuntimeError(f"Erreur d'impression : {e}") from e
