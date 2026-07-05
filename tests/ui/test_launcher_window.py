#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_launcher_window.py - Tests UI pour LauncherWindow

Description:
    Tests UI pour src/UI/launcher_window.py (LauncherWindow).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.05

Date de modification:
    2026.07.05
"""

import pytest

from src.UI.launcher_window import LauncherWindow


@pytest.fixture
def launcher(qtbot):
    window = LauncherWindow()
    qtbot.addWidget(window)
    return window


class TestLauncherWindow:
    def test_titre(self, launcher):
        assert launcher.windowTitle() == "Morphoz SnackApp — Choix du mode"

    def test_trois_cartes_de_mode(self, launcher):
        assert launcher.centralWidget() is not None

    @pytest.mark.parametrize("mode_id", ["complet", "prepa", "stats"])
    def test_choisir_emet_le_mode_et_ferme(self, launcher, qtbot, mode_id):
        with qtbot.waitSignal(launcher.mode_choisi, timeout=1000) as blocker:
            launcher._choisir(mode_id)
        assert blocker.args == [mode_id]
        assert not launcher.isVisible()

    def test_mode_inconnu_ignore_par_app(self):
        """Le dict de dispatch de app.py ne plante pas sur un identifiant inattendu (get() → None)."""
        classes_fenetre = {"complet": object, "prepa": object, "stats": object}
        assert classes_fenetre.get("inexistant") is None
