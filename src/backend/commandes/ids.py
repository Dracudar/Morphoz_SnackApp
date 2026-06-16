#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ids.py

Description:
    Cache des identifiants journaliers (commande et plats). Le cache est
    maintenu en mémoire et persisté sur disque à chaque création ou
    annulation d'identifiant pour éviter les décalages après un redémarrage.

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

        # Migration : anciennes clés par nom de type → clés par lettre
        for type_nom, lettre in PREFIXES_PLAT.items():
            if type_nom in valeur:
                if lettre not in valeur:
                    valeur[lettre] = valeur.pop(type_nom)
                else:
                    del valeur[type_nom]

        # Nettoyer les clés par nom de type inconnues restantes (ex. "café", "mr. freeze")
        for cle in [k for k in valeur if k != "commande" and len(k) > 1 and k == k.lower()]:
            del valeur[cle]

        # Initialiser les lettres connues
        for lettre in PREFIXES_PLAT.values():
            valeur.setdefault(lettre, 0)

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
        """Incrémente le compteur du type de plat, le persiste et retourne l'ID (ex: P001).

        Résolution du préfixe :
        1. PREFIXES_PLAT (plats historiques codés en dur)
        2. Champ "Lettre_ID" dans la carte active (nouveaux plats sans code)
        3. Repli sur "X" si rien n'est défini
        """
        cle = type_plat.lower()
        prefixe = PREFIXES_PLAT.get(cle)

        if prefixe is None:
            from src.backend.data.carte import get_card_data
            prefixe = get_card_data().get(type_plat, {}).get("Lettre_ID", "X")

        self._data[prefixe] = self._data.get(prefixe, 0) + 1
        self.save()
        return f"{prefixe}{self._data[prefixe]:03d}"


# ── Singleton ──────────────────────────────────────────────────────────────────

_id_cache: "DerniersIDCache | None" = None


def get_id_cache() -> DerniersIDCache:
    """
    Retourne le singleton DerniersIDCache.
    Recrée automatiquement le cache si le jour a changé (passage minuit).
    """
    global _id_cache
    from src.backend.config.chemins import get_logs_folder_path
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
