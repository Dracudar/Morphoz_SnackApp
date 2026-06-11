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
    1.7

Date de création:
    2026.06.09

Date de modification:
    2026.06.10
"""

import json
import shutil
from datetime import datetime
from pathlib import Path


# ── Constantes d'événements ────────────────────────────────────────────────────

AJOUT_PLAT = "AJOUT_PLAT"
ANNULATION_PLAT = "ANNULATION_PLAT"
ANNULATION_COMMANDE = "ANNULATION_COMMANDE"
VALIDATION_COMMANDE = "VALIDATION_COMMANDE"
PLAT_PRET = "PLAT_PRET"
PLAT_LIVRE = "PLAT_LIVRE"
PLAT_NON_LIVRE = "PLAT_NON_LIVRE"
TRANSFERT_PRET = "TRANSFERT_PRET"
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
IMPRESSION_TICKET = "IMPRESSION_TICKET"
AFFICHAGE_EXTERIEUR = "AFFICHAGE_EXTERIEUR"
CREATION_FICHIER = "CREATION_FICHIER"
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
    PLAT_NON_LIVRE: "commande",
    TRANSFERT_PRET: "commande",
    COMMANDE_TERMINEE: "commande",
    FICHIER_CORROMPU: "systeme",
    MODIFICATION_STOCK_MANUELLE: "stock",
    MODIFICATION_CACHE_STOCK: "stock",
    PERSISTANCE_STOCK: "stock",
    MODIFICATION_CARTE_MANUELLE: "carte",
    MODIFICATION_PARAMETRES_IMPRIMANTE: "parametres",
    MODIFICATION_OPTIONS_IMPRESSION: "parametres",
    MODIFICATION_DOSSIER_DONNEES: "parametres",
    IMPRESSION_TICKET: "commande",
    AFFICHAGE_EXTERIEUR: "systeme",
    CREATION_FICHIER: "systeme",
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

def migrer_log_journalier(ancien_dossier: Path, nouveau_dossier: Path) -> None:
    """Déplace ou fusionne le fichier de log du jour dans le nouveau dossier logs.

    Appelée lors d'un changement de dossier data pour assurer la continuité du suivi.
    - Nouveau dossier sans fichier log du jour → déplacement (move) du fichier source.
    - Fichier déjà présent → fusion avec déduplication par (timestamp, evenement, details),
      tri chronologique et réindexation.
    """
    global _log_index, _log_index_date

    today = datetime.now().strftime("%Y%m%d")
    ancien_fichier = Path(ancien_dossier) / f"app_{today}.log"

    if not ancien_fichier.exists():
        return

    def _lire(chemin: Path) -> list:
        entrees = []
        try:
            with chemin.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entrees.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except OSError:
            pass
        return entrees

    try:
        Path(nouveau_dossier).mkdir(parents=True, exist_ok=True)
        nouveau_fichier = Path(nouveau_dossier) / f"app_{today}.log"

        if not nouveau_fichier.exists():
            # Déplacement : le fichier source disparaît, pas de doublon possible
            shutil.move(str(ancien_fichier), nouveau_fichier)
        else:
            # Fusion avec déduplication pour éviter les doublons lors d'aller-retours
            def _cle(e: dict) -> tuple:
                return (
                    e.get("timestamp", ""),
                    e.get("evenement", ""),
                    json.dumps(e.get("details", {}), sort_keys=True, ensure_ascii=False),
                )

            vus: set = set()
            uniques: list = []
            for entree in _lire(ancien_fichier) + _lire(nouveau_fichier):
                cle = _cle(entree)
                if cle not in vus:
                    vus.add(cle)
                    uniques.append(entree)

            uniques.sort(key=lambda e: e.get("timestamp", ""))
            for i, entree in enumerate(uniques, start=1):
                entree["index"] = i

            with nouveau_fichier.open("w", encoding="utf-8") as f:
                for entree in uniques:
                    f.write(json.dumps(entree, ensure_ascii=False) + "\n")

            # Resynchroniser le compteur pour que les prochains index soient continus
            _log_index = len(uniques)
            _log_index_date = today

    except OSError:
        pass


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
