#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
commandes_utils.py

Description:
    Utilitaires pour la gestion des commandes : cache des identifiants journaliers
    (commande et plats), chargement de fichiers JSON avec gestion des erreurs.
    Le cache est maintenu en mémoire et persisté sur disque uniquement à la
    validation de la commande, comme le cache de stock.

Author :
    Dracudar

Version:
    3.1

Date de création :
    2025.05.31

Date de modification:
    2026.06.09
"""

import os
from datetime import datetime
import json

# Préfixe par type de plat pour les ID_plat (P001, G001, etc.)
PREFIXES_PLAT = {
    "pizza": "P",
    "grillade": "G",
    "frites": "F",
    "salade composée": "S",
    "crêpe": "C",
}


class DerniersIDCache:
    """
    Cache mémoire des compteurs d'identifiants journaliers (commandes et plats).
    Persisté sur disque à chaque création ou annulation d'identifiant pour éviter
    les décalages après un redémarrage sans validation.
    Migration transparente depuis l'ancien fichier 'dernier_id.json'.
    """

    _FILENAME = "derniers_ID.json"
    _FILENAME_OLD = "dernier_id.json"

    def __init__(self, logs_path: str):
        self._logs_path = logs_path
        self._date = datetime.now().strftime("%Y%m%d")
        self._data = self._load()

    def _load(self) -> dict:
        for filename in [self._FILENAME, self._FILENAME_OLD]:
            log_file = os.path.join(self._logs_path, filename)
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    contenu = json.load(f)
                valeur = contenu.get(self._date, {})
                # Migration ancien format : {"20260606": 8} → {"20260606": {"commande": 8, ...}}
                if isinstance(valeur, int):
                    valeur = {"commande": valeur}
                break
        else:
            valeur = {}

        valeur.setdefault("commande", 0)
        for cle in PREFIXES_PLAT:
            valeur.setdefault(cle, 0)
        return valeur

    def save(self):
        """Persiste les compteurs sur disque."""
        os.makedirs(self._logs_path, exist_ok=True)
        log_file = os.path.join(self._logs_path, self._FILENAME)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump({self._date: self._data}, f, indent=4, ensure_ascii=False)

    # ── Commande ──────────────────────────────────────────────────────────────

    def prochain_id_commande(self) -> str:
        """Incrémente le compteur commande, le persiste sur disque et retourne le nouvel ID (aaaammjj-000)."""
        self._data["commande"] += 1
        self.save()
        return f"{self._date}-{self._data['commande']:03d}"

    def decrementer_commande(self):
        """Décrémente le compteur commande (annulation en saisie) et persiste sur disque."""
        if self._data["commande"] > 0:
            self._data["commande"] -= 1
            self.save()

    # ── Plats ─────────────────────────────────────────────────────────────────

    def prochain_id_plat(self, type_plat: str) -> str:
        """Incrémente le compteur du type de plat, le persiste et retourne l'ID (ex: P001)."""
        cle = type_plat.lower()
        prefixe = PREFIXES_PLAT.get(cle, "X")
        self._data[cle] = self._data.get(cle, 0) + 1
        self.save()
        return f"{prefixe}{self._data[cle]:03d}"

    def decrementer_plat(self, type_plat: str, id_plat_val: str):
        """
        Décrémente le compteur du type de plat, uniquement si id_plat_val correspond
        au dernier identifiant assigné (évite les trous en cas de non-dernier plat).
        """
        cle = type_plat.lower()
        try:
            numero = int(id_plat_val[1:])  # "P005" → 5
        except (ValueError, IndexError):
            return
        compteur = self._data.get(cle, 0)
        if numero == compteur and compteur > 0:
            self._data[cle] -= 1
            self.save()


# ── Singleton ──────────────────────────────────────────────────────────────────

_id_cache: "DerniersIDCache | None" = None


def get_id_cache() -> DerniersIDCache:
    """
    Retourne le singleton DerniersIDCache.
    Recrée automatiquement le cache si le jour a changé (passage minuit).
    """
    global _id_cache
    from src.backend.app_config import get_logs_folder_path
    date_actuelle = datetime.now().strftime("%Y%m%d")
    if _id_cache is None or _id_cache._date != date_actuelle:
        _id_cache = DerniersIDCache(str(get_logs_folder_path()))
    return _id_cache


# ── API publique (compatibilité descendante avec les appelants existants) ──────

def generer_ID_commande(logs_path=None, commandes_path=None) -> str:
    """Génère un identifiant unique pour une commande au format aaaammjj-000."""
    return get_id_cache().prochain_id_commande()


def generer_ID_plat(type_plat: str, logs_path=None) -> str:
    """Génère un identifiant de plat du jour au format X000 (ex: P001, G002)."""
    return get_id_cache().prochain_id_plat(type_plat)


def decrementer_ID_commande(logs_path=None):
    """Décrémente le compteur commande (annulation en saisie, non persisté)."""
    get_id_cache().decrementer_commande()


def decrementer_ID_plat(type_plat: str, id_plat_val: str, logs_path=None):
    """Décrémente le compteur d'un type de plat si c'est le dernier assigné."""
    get_id_cache().decrementer_plat(type_plat, id_plat_val)


# ── Chargement JSON ────────────────────────────────────────────────────────────

def charger_fichier_commande(chemin_fichier):
    """
    Charge un fichier JSON avec gestion des erreurs.

    :param chemin_fichier: Chemin vers le fichier JSON.
    :return: Contenu du fichier sous forme de dictionnaire ou None si une erreur survient.
    """
    if not os.path.exists(chemin_fichier):
        print(f"Erreur : Le fichier '{chemin_fichier}' est introuvable.")
        return None

    try:
        with open(chemin_fichier, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier '{chemin_fichier}' contient des données invalides.")
        dossier_corrompu = os.path.join(os.path.dirname(chemin_fichier), "corrompu")
        os.makedirs(dossier_corrompu, exist_ok=True)
        os.rename(chemin_fichier, os.path.join(dossier_corrompu, os.path.basename(chemin_fichier)))
        return None
