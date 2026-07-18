#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_interface_principale.py - Tests UI pour InterfacePrincipaleWidget

Description:
    Tests UI pour src/UI/view/interface_principale.py : page de démarrage
    conditionnelle selon que le dossier data est déjà configuré ou non
    (typiquement défini depuis le launcher avant l'ouverture de ce mode).

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

from src.mod.saisie.UI.interface_principale import InterfacePrincipaleWidget


class TestPageDeDemarrage:
    def test_demarre_sur_saisie_si_dossier_configure(self, qtbot, monkeypatch):
        monkeypatch.setattr(
            "src.mod.saisie.UI.interface_principale.data_folder_est_configure", lambda: True
        )
        widget = InterfacePrincipaleWidget()
        qtbot.addWidget(widget)
        assert widget.left_stack.currentWidget() is widget.page_saisie

    def test_demarre_sur_parametres_si_dossier_non_configure(self, qtbot, monkeypatch):
        monkeypatch.setattr(
            "src.mod.saisie.UI.interface_principale.data_folder_est_configure", lambda: False
        )
        widget = InterfacePrincipaleWidget()
        qtbot.addWidget(widget)
        assert widget.left_stack.currentWidget() is widget.page_parametres
