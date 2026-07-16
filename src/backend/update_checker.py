#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_checker.py - Vérification des mises à jour disponibles sur GitHub

Description:
    Vérifie en arrière-plan si une nouvelle version est disponible sur GitHub
    (dépôt dracudar/morphoz_snackapp) via l'API Releases. Émet un signal
    PySide6 avec le résultat une fois la vérification terminée.

Author :
    Dracudar

Version:
    1.2

Date de création :
    2026.06.14

Date de modification:
    2026.07.16
"""

import json
import urllib.request
from urllib.error import URLError

from PySide6.QtCore import QThread, Signal

_GITHUB_API_URL = "https://api.github.com/repos/dracudar/morphoz_snackapp/releases/latest"
_TIMEOUT = 5

# Référence forte sur les vérifications en cours : run() bloque sur un appel réseau
# (pas de boucle d'événements à interrompre proprement), donc si la fenêtre qui l'a
# lancée est fermée entre-temps, ce fil ne doit pas être détruit pendant qu'il tourne
# encore (crash Qt) — il reste ici jusqu'à sa fin naturelle (au pire le timeout réseau).
_verifications_en_cours: set = set()


def _parse_version(v: str) -> tuple:
    """Convertit une chaîne de version (ex. 'v2.1.0') en tuple comparable."""
    try:
        return tuple(int(x) for x in v.lstrip("v").strip().split("."))
    except ValueError:
        return (0, 0, 0)


class UpdateChecker(QThread):
    """Vérifie en arrière-plan si une nouvelle version est disponible sur GitHub."""

    update_available = Signal(str)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self._current_version = current_version

    def start(self, *args, **kwargs):
        """Démarre la vérification en gardant une référence forte jusqu'à la fin.

        Ainsi la fenêtre appelante peut être fermée/détruite (ex. WA_DeleteOnClose)
        sans risquer de détruire ce fil pendant qu'il tourne encore.
        """
        _verifications_en_cours.add(self)
        self.finished.connect(lambda: _verifications_en_cours.discard(self))
        super().start(*args, **kwargs)

    def run(self):
        try:
            req = urllib.request.Request(
                _GITHUB_API_URL,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "MorphozSnackApp",
                },
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))

            tag = data.get("tag_name", "")
            if tag and _parse_version(tag) > _parse_version(self._current_version):
                self.update_available.emit(tag.lstrip("v"))

        except (URLError, OSError, KeyError, ValueError):
            pass


def attendre_verifications_en_cours(timeout_ms: int = 6000) -> None:
    """Attend la fin des vérifications encore en cours (au plus timeout_ms chacune).

    À appeler juste avant la fermeture définitive de l'application (ex. sur
    QApplication.aboutToQuit) : sans cela, si le processus se termine pendant
    qu'un fil de vérification tourne encore, Qt/PySide peut planter en le
    détruisant en cours d'exécution.
    """
    for checker in list(_verifications_en_cours):
        checker.wait(timeout_ms)
