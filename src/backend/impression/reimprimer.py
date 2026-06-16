#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reimprimer.py

Description:
    Réimpression manuelle des tickets récapitulatif et cuisine depuis
    l'historique, indépendante des options d'impression automatique.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.16

Date de modification:
    2026.06.16
"""

from src.backend.commandes.stock_utils import charger_fichier_commande
from src.backend.impression.tickets import _do_print_recap, _get_printer, _print_plat_ticket
from src.backend import logger


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
