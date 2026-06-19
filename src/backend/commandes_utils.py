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
    3.4

Date de création :
    2025.05.31

Date de modification:
    2026.06.15
"""

import json
import os
from contextlib import contextmanager
from datetime import datetime
from src.backend import file_io, logger

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

    def _chemin_fichier(self) -> str:
        """Chemin du fichier de compteurs (utilisé pour la persistance et le verrou)."""
        return os.path.join(self._logs_path, self._FILENAME)

    def _load(self) -> dict:
        for filename in [self._FILENAME, self._FILENAME_OLD]:
            log_file = os.path.join(self._logs_path, filename)
            if os.path.exists(log_file):
                contenu = file_io.charger_json(log_file)
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
        """Persiste les compteurs sur disque (écriture atomique)."""
        file_io.sauvegarder_json(self._chemin_fichier(), {self._date: self._data})

    # ── Commande ──────────────────────────────────────────────────────────────

    def prochain_id_commande(self) -> str:
        """
        Incrémente le compteur commande, le persiste sur disque et retourne le
        nouvel ID (aaaammjj-000).

        Recharge la valeur la plus récente depuis le disque sous verrou avant
        d'incrémenter : plusieurs postes du réseau local peuvent générer un ID
        le même jour, donc le compteur gardé en mémoire seul produirait des
        doublons si un autre poste a incrémenté entre-temps.
        """
        with file_io.verrou_fichier(self._chemin_fichier()):
            self._data = self._load()
            self._data["commande"] += 1
            self.save()
        return f"{self._date}-{self._data['commande']:03d}"

    def decrementer_commande(self):
        """Décrémente le compteur commande (annulation en saisie) et persiste sur disque."""
        with file_io.verrou_fichier(self._chemin_fichier()):
            self._data = self._load()
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

        Comme `prochain_id_commande`, recharge la valeur depuis le disque sous
        verrou avant d'incrémenter (même risque de doublon entre postes).
        """
        cle = type_plat.lower()
        prefixe = PREFIXES_PLAT.get(cle)

        if prefixe is None:
            from src.backend.data_sources import get_card_data
            prefixe = get_card_data().get(type_plat, {}).get("Lettre_ID", "X")

        with file_io.verrou_fichier(self._chemin_fichier()):
            self._data = self._load()
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


# ── Utilitaires stock et annulation ───────────────────────────────────────────

def restaurer_stock_plat(plat: dict) -> None:
    """Restitue dans le cache les quantités consommées par un plat annulé."""
    from src.backend.data_sources import get_stock_cache
    cache = get_stock_cache()
    plat_type = plat.get("Plat", "")
    composition = plat.get("Composition", {})
    if plat_type == "Pizza":
        cache.incrementer(["Plats", "Pizza", "Pâte à pizza"])
    elif plat_type == "Grillade":
        for viande, qte in composition.get("Viandes", {}).items():
            cache.incrementer(["Plats", "Grillades", viande], qte)


def log_stock_restauration(plat: dict, id_commande: str) -> None:
    """Log la restauration automatique de stock lors de l'annulation d'un plat."""
    type_plat = plat.get("Plat", "")
    if type_plat == "Pizza":
        logger.log(logger.MODIFICATION_CACHE_STOCK, {
            "raison": "annulation_plat",
            "id_commande": id_commande,
            "id_plat": plat.get("ID", ""),
            "type_plat": "Pizza",
            "nom_plat": plat.get("Nom", ""),
            "modifications": [{"chemin": ["Plats", "Pizza", "Pâte à pizza"], "delta": +1}],
        })
    elif type_plat == "Grillade":
        viandes = plat.get("Composition", {}).get("Viandes", {})
        if viandes:
            logger.log(logger.MODIFICATION_CACHE_STOCK, {
                "raison": "annulation_plat",
                "id_commande": id_commande,
                "id_plat": plat.get("ID", ""),
                "type_plat": "Grillade",
                "nom_plat": plat.get("Nom", ""),
                "modifications": [
                    {"chemin": ["Plats", "Grillades", viande], "delta": +qte}
                    for viande, qte in viandes.items()
                ],
            })


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
    from src.backend.app_config import get_command_root

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
        data = file_io.charger_json(order_file)
        if not data:
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


# ── Chargement JSON ────────────────────────────────────────────────────────────

def charger_fichier_commande(chemin_fichier):
    """
    Charge un fichier JSON avec gestion des erreurs.

    :param chemin_fichier: Chemin vers le fichier JSON.
    :return: Contenu du fichier sous forme de dictionnaire ou None si une erreur survient.
    """
    if not os.path.exists(chemin_fichier):
        print(f"Erreur : Le fichier '{chemin_fichier}' est introuvable.")
        logger.log(logger.ERREUR, {
            "contexte": "lecture_commande",
            "message": "Fichier introuvable",
            "chemin": chemin_fichier,
        })
        return None

    try:
        with open(chemin_fichier, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
    except json.JSONDecodeError:
        print(f"Erreur : Le fichier '{chemin_fichier}' contient des données invalides.")
        dossier_corrompu = os.path.join(os.path.dirname(chemin_fichier), "corrompu")
        os.makedirs(dossier_corrompu, exist_ok=True)
        chemin_destination = os.path.join(dossier_corrompu, os.path.basename(chemin_fichier))
        os.rename(chemin_fichier, chemin_destination)
        logger.log(logger.FICHIER_CORROMPU, {
            "chemin_original": chemin_fichier,
            "chemin_destination": chemin_destination,
        })
        return None


def sauvegarder_fichier_commande(chemin_fichier, commande: dict) -> bool:
    """
    Sauvegarde un fichier de commande de façon atomique (fichier temporaire +
    remplacement), pour ne jamais laisser un JSON à moitié écrit en cas de
    crash ou de coupure réseau en plein milieu de l'écriture.

    :param chemin_fichier: Chemin vers le fichier JSON de la commande.
    :param commande: Contenu à sauvegarder.
    :return: True si la sauvegarde a réussi.
    """
    return file_io.sauvegarder_json(chemin_fichier, commande)


@contextmanager
def acceder_commande(chemin_fichier):
    """
    Verrouille un fichier de commande partagé, le charge, le fournit pour
    modification, puis le sauvegarde de façon atomique en sortie de bloc.

    Plusieurs postes du réseau local (caisse, cuisine, suivi...) peuvent ouvrir
    le même fichier de commande en même temps (ex. la cuisine marque un plat
    "Prêt" pendant que la caisse annule la commande) : sans verrou, le second
    qui sauvegarde écraserait la modification du premier sans le savoir. Le
    verrou garantit qu'un seul poste à la fois exécute la séquence
    "charger → modifier → sauvegarder" sur ce fichier.

    Fournit None si le fichier est introuvable ou corrompu : l'appelant doit
    vérifier avant de modifier, comme avec `charger_fichier_commande`.
    Si une exception est levée dans le bloc, rien n'est sauvegardé.

    Exemple :
        with acceder_commande(chemin_fichier) as commande:
            if not commande:
                return
            commande["Informations"]["Prioritaire"] = True
    """
    with file_io.verrou_fichier(chemin_fichier):
        commande = charger_fichier_commande(chemin_fichier)
        yield commande
        if commande is not None:
            sauvegarder_fichier_commande(chemin_fichier, commande)
