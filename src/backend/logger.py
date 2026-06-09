#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logger.py

Description:
    Journalisation des actions utilisateur.
    Chaque événement est enregistré dans un fichier journalier au format JSON Lines
    (data/logs/app_YYYYMMDD.log), un objet JSON par ligne.

    Format d'une entrée :
    {"index": 42, "timestamp": "2026-06-09T14:30:15", "categorie": "commande",
     "evenement": "AJOUT_PLAT", "details": {...}}

Author:
    Dracudar

Version:
    1.2

Date de création:
    2026.06.09

Date de modification:
    2026.06.09
"""

import json
from datetime import datetime
from pathlib import Path


# ── Constantes d'événements ────────────────────────────────────────────────────

AJOUT_PLAT = "AJOUT_PLAT"
ANNULATION_PLAT = "ANNULATION_PLAT"
ANNULATION_COMMANDE = "ANNULATION_COMMANDE"
VALIDATION_COMMANDE = "VALIDATION_COMMANDE"
PLAT_PRET = "PLAT_PRET"
PLAT_LIVRE = "PLAT_LIVRE"
COMMANDE_TERMINEE = "COMMANDE_TERMINEE"
FICHIER_CORROMPU = "FICHIER_CORROMPU"
MODIFICATION_STOCK_MANUELLE = "MODIFICATION_STOCK_MANUELLE"
MODIFICATION_CACHE_STOCK = "MODIFICATION_CACHE_STOCK"
PERSISTANCE_STOCK = "PERSISTANCE_STOCK"
MODIFICATION_CARTE_MANUELLE = "MODIFICATION_CARTE_MANUELLE"
MODIFICATION_PARAMETRES_IMPRIMANTE = "MODIFICATION_PARAMETRES_IMPRIMANTE"
MODIFICATION_OPTIONS_IMPRESSION = "MODIFICATION_OPTIONS_IMPRESSION"
MODIFICATION_DOSSIER_DONNEES = "MODIFICATION_DOSSIER_DONNEES"
CREATION_DOSSIER = "CREATION_DOSSIER"
DEMARRAGE_APP = "DEMARRAGE_APP"
ARRET_APP = "ARRET_APP"
ERREUR = "ERREUR"


# ── Catégories par événement ───────────────────────────────────────────────────

_CATEGORIES: dict = {
    AJOUT_PLAT: "commande",
    ANNULATION_PLAT: "commande",
    ANNULATION_COMMANDE: "commande",
    VALIDATION_COMMANDE: "commande",
    PLAT_PRET: "commande",
    PLAT_LIVRE: "commande",
    COMMANDE_TERMINEE: "commande",
    FICHIER_CORROMPU: "systeme",
    MODIFICATION_STOCK_MANUELLE: "stock",
    MODIFICATION_CACHE_STOCK: "stock",
    PERSISTANCE_STOCK: "stock",
    MODIFICATION_CARTE_MANUELLE: "carte",
    MODIFICATION_PARAMETRES_IMPRIMANTE: "parametres",
    MODIFICATION_OPTIONS_IMPRESSION: "parametres",
    MODIFICATION_DOSSIER_DONNEES: "parametres",
    CREATION_DOSSIER: "systeme",
    DEMARRAGE_APP: "systeme",
    ARRET_APP: "systeme",
    ERREUR: "erreur",
}


# ── Compteur d'index journalier ────────────────────────────────────────────────

_log_index: int = 0
_log_index_date: str = ""


def _next_index(today: str, log_file: Path) -> int:
    """Retourne le prochain numéro de séquence pour le fichier du jour.

    Initialise le compteur en comptant les entrées existantes du fichier
    au premier appel de la journée, pour assurer la continuité après un
    redémarrage de l'application.
    """
    global _log_index, _log_index_date
    if _log_index_date != today:
        _log_index = 0
        if log_file.exists():
            try:
                with log_file.open("r", encoding="utf-8") as f:
                    _log_index = sum(1 for line in f if line.strip())
            except OSError:
                pass
        _log_index_date = today
    _log_index += 1
    return _log_index


# ── API publique ───────────────────────────────────────────────────────────────

def log(evenement: str, details: dict = None) -> None:
    """Enregistre un événement dans le fichier de log journalier (data/logs/app_YYYYMMDD.log).

    Ne lève jamais d'exception : les erreurs disque sont silencieusement ignorées
    pour ne pas interrompre le flux applicatif.
    """
    from src.backend.app_config import get_logs_folder_path

    now = datetime.now()
    today = now.strftime("%Y%m%d")
    logs_folder = get_logs_folder_path()

    try:
        logs_folder.mkdir(parents=True, exist_ok=True)
        log_file = logs_folder / f"app_{today}.log"
        entree = {
            "index": _next_index(today, log_file),
            "timestamp": now.isoformat(timespec="seconds"),
            "categorie": _CATEGORIES.get(evenement, "autre"),
            "evenement": evenement,
            "details": details or {},
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entree, ensure_ascii=False) + "\n")
    except OSError:
        pass
