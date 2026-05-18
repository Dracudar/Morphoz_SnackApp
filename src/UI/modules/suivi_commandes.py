#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suivi_commandes.py - Module de suivi des commandes

Description:
    Bloc lateral de suivi des commandes en cours de preparation.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout

from src.UI.widgets.conteneur_suivi_commande import ConteneurSuiviCommande


class SuiviCommandesModule(QFrame):
    """Bloc d'affichage des commandes en cours."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("suiviCommandesModule")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tracker = ConteneurSuiviCommande(self)
        layout.addWidget(self.tracker)
