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
    1.0

Date de création :
    2026.06.14

Date de modification:
    2026.06.14
"""

import json
import urllib.request
from urllib.error import URLError

from PySide6.QtCore import QThread, Signal

_GITHUB_API_URL = "https://api.github.com/repos/dracudar/morphoz_snackapp/releases/latest"
_TIMEOUT = 5


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
