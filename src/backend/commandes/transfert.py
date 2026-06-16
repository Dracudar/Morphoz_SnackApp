#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transfert.py

Description:
    Recherche d'un plat identique "En préparation" à qui transférer l'état
    "Prêt" lors de l'annulation d'un plat déjà prêt.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.16

Date de modification:
    2026.06.16
"""

import os
import json


def plats_identiques(plat_ref: dict, plat_candidat: dict) -> bool:
    """Vérifie si deux plats sont strictement identiques (type → recette/nom → composition)."""
    if plat_ref.get("Plat") != plat_candidat.get("Plat"):
        return False
    if plat_ref.get("Recette") != plat_candidat.get("Recette"):
        return False
    if plat_ref.get("Nom") != plat_candidat.get("Nom"):
        return False
    return plat_ref.get("Composition") == plat_candidat.get("Composition")


def trouver_candidat_transfert(plat_ref: dict, chemin_commande_source: str):
    """
    Cherche un plat identique "En préparation" à qui transférer l'état "Prêt".

    Ordre de priorité :
    1. Même commande (en premier)
    2. Autres commandes prioritaires (ordre ID croissant)
    3. Autres commandes (ordre ID croissant)

    Retourne (chemin_fichier, plat_id_complet) ou None si aucun candidat trouvé.
    """
    from src.backend.config.chemins import get_command_root

    root_folder = get_command_root()
    if root_folder is None:
        return None

    live_folder = None
    for folder_name in ("en_cours", "en-cours"):
        candidate = root_folder / folder_name
        if candidate.exists():
            live_folder = candidate
            break

    if live_folder is None:
        return None

    nom_source = os.path.basename(chemin_commande_source)
    meme_commande = []
    prioritaires = []
    autres = []

    for order_file in sorted(live_folder.glob("commande_*.json")):
        try:
            with open(str(order_file), "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        infos = data.get("Informations", {})
        est_prioritaire = bool(infos.get("Prioritaire", False))
        est_meme_commande = (order_file.name == nom_source)

        for plat in data.get("Commande", {}).values():
            if plat.get("Statut") != "En préparation":
                continue
            if not plats_identiques(plat_ref, plat):
                continue
            entree = (str(order_file), plat.get("ID", ""))
            if est_meme_commande:
                meme_commande.append(entree)
            elif est_prioritaire:
                prioritaires.append(entree)
            else:
                autres.append(entree)

    candidats = meme_commande + prioritaires + autres
    return candidats[0] if candidats else None
