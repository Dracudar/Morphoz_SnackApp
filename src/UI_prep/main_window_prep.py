#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window_prep.py - Fenêtre principale du poste de préparation allégé

Description:
    Fenêtre principale de l'application légère pour les postes de préparation.
    Composée d'un volet latéral de configuration minimal et de la vue du poste
    de préparation en plein écran.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.14

Date de modification:
    2026.06.14
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from src.modules.commandes_poste_preparation.UI.poste_preparation import PostePreparationModule
from src.UI_prep.panneau_lateral import PanneauLateral


class MainWindowPrep(QMainWindow):
    """Fenêtre principale du poste de préparation allégé."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Morphoz SnackApp — Poste de préparation")
        self.setGeometry(100, 100, 1200, 800)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._panneau = PanneauLateral(self)
        self._poste = PostePreparationModule()

        layout.addWidget(self._panneau)
        layout.addWidget(self._poste, 1)

        self.setCentralWidget(central)
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Configure les raccourcis clavier globaux."""
        quit_action = QAction("Quitter", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

        fs_action = QAction("Plein écran", self)
        fs_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        fs_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(fs_action)

        esc_action = QAction("Quitter plein écran", self)
        esc_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        esc_action.triggered.connect(self.exit_fullscreen)
        self.addAction(esc_action)

    def toggle_fullscreen(self):
        """Bascule le mode plein écran."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def exit_fullscreen(self):
        """Quitte le mode plein écran si actif."""
        if self.isFullScreen():
            self.showNormal()
