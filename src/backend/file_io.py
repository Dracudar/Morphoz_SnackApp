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
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Union

from filelock import FileLock, Timeout

from src.backend import logger

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
    """Charge un fichier JSON et retourne un dict, ou {} si absent ou invalide.

    Un échec de lecture (fichier corrompu, verrou réseau, montage indisponible...)
    est journalisé : un dict vide retourné silencieusement masquerait la cause
    réelle d'un dysfonctionnement en aval (ex. stock vide alors que le fichier
    existe mais n'a pas pu être lu).
    """
    chemin = Path(chemin)
    if not chemin.exists():
        return {}
    try:
        with chemin.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        logger.log(logger.ERREUR, {
            "contexte": "lecture_json",
            "chemin": str(chemin),
            "detail": str(e),
        })
        return {}
    return data if isinstance(data, dict) else {}


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
