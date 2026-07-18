#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file_io.py - Accès bas niveau aux fichiers JSON partagés

Description:
    Plusieurs postes (caisse, cuisine, suivi...) peuvent lire et écrire les mêmes
    fichiers JSON en même temps depuis le réseau local (stock, commandes, IDs
    journaliers). Ce module centralise deux garanties que les accès fichier
    "bruts" (open/json.load/json.dump) n'offrent pas :

    1. Écriture atomique : on écrit dans un fichier temporaire puis on le
       remplace d'un coup (os.replace), pour qu'un crash ou une coupure réseau
       en plein milieu de l'écriture ne laisse jamais un JSON à moitié écrit.
    2. Verrou inter-processus (et inter-machine sur un partage réseau) : le
       gestionnaire de contexte `acceder_json` empêche deux postes de lire,
       modifier puis écraser le même fichier en même temps (la modification du
       second écraserait celle du premier sans le savoir).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.19
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple, Union

from filelock import FileLock, Timeout

# Délai d'attente avant d'abandonner l'acquisition d'un verrou. Au-delà, on
# considère qu'un autre poste (ou un crash ayant laissé le verrou en place) bloque
# l'accès anormalement longtemps.
DELAI_VERROU_SECONDES = 15


def _chemin_verrou(chemin: Path) -> str:
    """Chemin du fichier de verrou associé à un fichier de données."""
    return str(chemin.with_name(chemin.name + ".lock"))


def verrou_fichier(chemin: Union[str, Path]) -> FileLock:
    """
    Verrou inter-processus sur un fichier JSON partagé.

    À utiliser autour de toute séquence "charger → modifier → sauvegarder" pour
    qu'un seul poste à la fois puisse exécuter cette séquence sur un fichier donné.
    """
    return FileLock(_chemin_verrou(Path(chemin)), timeout=DELAI_VERROU_SECONDES)


def charger_json(chemin: Union[str, Path]) -> Dict[str, Any]:
    """Charge un fichier JSON et retourne un dict, ou {} si absent ou invalide."""
    chemin = Path(chemin)
    if not chemin.exists():
        return {}
    try:
        with chemin.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


# ── Cache de lecture mtime ─────────────────────────────────────────────────────
#
# Les affichages à rafraîchissement automatique (suivi, préparation, historique,
# logs, stock) relisent en boucle les mêmes fichiers, le plus souvent inchangés,
# depuis un partage réseau. `charger_json_cache` évite de re-parser un fichier
# dont le couple (mtime, taille) n'a pas bougé : un simple `stat()` (peu coûteux,
# même en réseau) suffit alors, et le payload mémorisé est renvoyé tel quel.
#
# IMPORTANT : le dict renvoyé est PARTAGÉ avec le cache. Les appelants ne doivent
# pas le muter (les agrégateurs de data_sources se contentent de le lire et
# construisent de nouveaux dicts). Pour une séquence lecture→modification→écriture,
# utiliser `acceder_json`, qui relit toujours le disque sous verrou (non caché).

# {chemin: (mtime_ns, taille, payload)}
_cache_lecture: Dict[str, Tuple[int, int, Dict[str, Any]]] = {}
_cache_lecture_lock = threading.Lock()


def charger_json_cache(chemin: Union[str, Path]) -> Dict[str, Any]:
    """Charge un JSON via un cache indexé sur (mtime, taille) ; ne re-parse que si le fichier a changé.

    Retourne `{}` si le fichier est absent ou invalide (et purge alors l'entrée de
    cache). Le dict renvoyé est partagé avec le cache : NE PAS le muter.
    """
    chemin = Path(chemin)
    cle = str(chemin)
    try:
        st = chemin.stat()
    except OSError:
        with _cache_lecture_lock:
            _cache_lecture.pop(cle, None)
        return {}

    mtime_ns, taille = st.st_mtime_ns, st.st_size
    with _cache_lecture_lock:
        entree = _cache_lecture.get(cle)
        if entree is not None and entree[0] == mtime_ns and entree[1] == taille:
            return entree[2]

    # Lecture/parse hors verrou (I/O potentiellement réseau). Les écritures étant
    # atomiques (os.replace), on lit toujours une version complète, jamais tronquée.
    data = charger_json(chemin)
    with _cache_lecture_lock:
        _cache_lecture[cle] = (mtime_ns, taille, data)
    return data


def signature_fichier(chemin: Union[str, Path]) -> Optional[Tuple[int, int]]:
    """Retourne (mtime_ns, taille) d'un fichier, ou None s'il est absent/inaccessible.

    Sert à détecter d'un tick à l'autre si un fichier unique (stock, log) a changé,
    sans en lire le contenu.
    """
    try:
        st = Path(chemin).stat()
    except OSError:
        return None
    return (st.st_mtime_ns, st.st_size)


def signature_dossier(
    dossier: Union[str, Path], motif: str = "commande_*.json"
) -> Tuple[Tuple[str, int], ...]:
    """Retourne la signature d'un dossier : tuple trié de (nom, mtime_ns) sans rien parser.

    Deux signatures identiques d'un tick à l'autre garantissent qu'aucun fichier
    correspondant au motif n'a été ajouté, supprimé ni modifié — le module peut
    alors court-circuiter son rafraîchissement.
    """
    dossier = Path(dossier)
    if not dossier.exists():
        return ()
    entrees = []
    for fichier in dossier.glob(motif):
        try:
            entrees.append((fichier.name, fichier.stat().st_mtime_ns))
        except OSError:
            continue
    entrees.sort()
    return tuple(entrees)


def elaguer_cache_dossier(dossier: Union[str, Path], noms_presents: Iterable[str]) -> None:
    """Retire du cache les entrées d'un dossier dont le fichier n'est plus présent.

    Appelé par les agrégateurs après avoir listé le dossier : borne la RAM sur un
    événement long, où les commandes migrent de `en_cours/` vers `terminee/`.
    """
    dossier = str(Path(dossier))
    presents = set(noms_presents)
    with _cache_lecture_lock:
        for cle in list(_cache_lecture.keys()):
            chemin = Path(cle)
            if str(chemin.parent) == dossier and chemin.name not in presents:
                _cache_lecture.pop(cle, None)


def vider_cache_lecture() -> None:
    """Vide entièrement le cache de lecture.

    À appeler quand le dossier de données change (Paramètres) : les anciens chemins
    n'ont plus de sens.
    """
    with _cache_lecture_lock:
        _cache_lecture.clear()


def sauvegarder_json(chemin: Union[str, Path], payload: Dict[str, Any]) -> bool:
    """
    Écrit un dict en JSON de façon atomique (fichier temporaire + remplacement).

    N'acquiert aucun verrou : à utiliser seul uniquement pour une écriture isolée
    (ex. sauvegarde d'une carte éditée par un seul poste à la fois). Pour une
    séquence "charger → modifier → sauvegarder" sur un fichier partagé, préférer
    `acceder_json`.
    """
    chemin = Path(chemin)
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        fd, nom_temp = tempfile.mkstemp(
            dir=str(chemin.parent), prefix=f".{chemin.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=4)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(nom_temp, chemin)
        except OSError:
            os.unlink(nom_temp)
            raise
    except OSError:
        return False
    return True


@contextmanager
def acceder_json(chemin: Union[str, Path]) -> Iterator[Dict[str, Any]]:
    """
    Verrouille un fichier JSON partagé, charge SA DERNIÈRE version sur disque,
    la fournit pour modification, puis la sauvegarde de façon atomique en sortie
    de bloc — le tout sans qu'un autre poste puisse intervenir entre les deux.

    Exemple :
        with acceder_json(chemin_fichier) as commande:
            commande["Informations"]["Prioritaire"] = True
        # sauvegardé automatiquement ici, verrou relâché

    Si une exception est levée dans le bloc, rien n'est sauvegardé (le verrou est
    quand même relâché) : on évite de persister un état partiellement modifié.

    :raises filelock.Timeout: si un autre poste garde le verrou plus de
        DELAI_VERROU_SECONDES (signe d'un blocage anormal, à ne pas avaler
        silencieusement).
    """
    chemin = Path(chemin)
    with verrou_fichier(chemin):
        data = charger_json(chemin)
        yield data
        sauvegarder_json(chemin, data)
