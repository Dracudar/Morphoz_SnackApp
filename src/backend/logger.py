#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logger.py

Description:
    Journalisation des actions utilisateur.
    Chaque événement est enregistré dans un fichier journalier au format JSON Lines
    (data/logs/app_YYYYMMDD.log), un objet JSON par ligne.

Author:
    Dracudar

Version:
    1.0

Date de création:
    2026.06.09
"""

import json
from datetime import datetime


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
MODIFICATION_STOCK_AUTOMATIQUE = "MODIFICATION_STOCK_AUTOMATIQUE"
MODIFICATION_CARTE_MANUELLE = "MODIFICATION_CARTE_MANUELLE"


# ── API publique ───────────────────────────────────────────────────────────────

def log(evenement: str, details: dict = None) -> None:
    """Enregistre un événement dans le fichier de log journalier (data/logs/app_YYYYMMDD.log).

    Ne lève jamais d'exception : les erreurs disque sont silencieusement ignorées
    pour ne pas interrompre le flux applicatif.
    """
    from src.backend.app_config import get_logs_folder_path

    now = datetime.now()
    logs_folder = get_logs_folder_path()

    try:
        logs_folder.mkdir(parents=True, exist_ok=True)
        log_file = logs_folder / f"app_{now.strftime('%Y%m%d')}.log"
        entree = {
            "timestamp": now.isoformat(timespec="seconds"),
            "evenement": evenement,
            "details": details or {},
        }
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entree, ensure_ascii=False) + "\n")
    except OSError:
        pass
