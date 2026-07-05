#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_main_window_stats.py - Tests UI pour MainWindowStats

Description:
    Tests UI pour src/UI_stats/main_window_stats.py (MainWindowStats), la vue
    allégée Historique + Statistiques choisie depuis le launcher.

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

from src.UI_stats.main_window_stats import MainWindowStats


@pytest.fixture
def window(qtbot):
    w = MainWindowStats()
    qtbot.addWidget(w)
    return w


class TestMainWindowStats:
    def test_titre(self, window):
        assert window.windowTitle() == "Morphoz SnackApp — Historique / Statistiques"

    def test_page_par_defaut_est_historique(self, window):
        assert window.left_stack.currentWidget() is window.page_historique

    def test_set_page_bascule_vers_stats(self, window):
        window.set_page("stats")
        assert window.left_stack.currentWidget() is window.page_stats

    def test_set_page_id_inconnu_ne_change_rien(self, window):
        window.set_page("stats")
        window.set_page("inexistant")
        assert window.left_stack.currentWidget() is window.page_stats

    def test_go_back_historique_ramene_a_historique(self, window):
        window.set_page("stats")
        window.page_historique.go_back.emit()
        assert window.left_stack.currentWidget() is window.page_historique

    def test_go_back_stats_ramene_a_historique(self, window):
        window.set_page("stats")
        window.page_stats.go_back.emit()
        assert window.left_stack.currentWidget() is window.page_historique

    def test_maj_page_active_reflete_le_volet(self, window):
        window.set_page("stats")
        assert window._volet._boutons_nav["stats"].isChecked()
        assert not window._volet._boutons_nav["historique"].isChecked()


class TestPleinEcran:
    def test_toggle_active_plein_ecran(self, window):
        assert not window.isFullScreen()
        window.toggle_fullscreen()
        assert window.isFullScreen()

    def test_exit_fullscreen_depuis_plein_ecran(self, window):
        window.showFullScreen()
        window.exit_fullscreen()
        assert not window.isFullScreen()
