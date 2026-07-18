#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window.py - Main Window Module

Description:
    This module contains the main window implementation for the Morphoz SnackApp UI.

Author :
    Dracudar

Version:
    2.6

Date de création :
    2026.05.12

Date de modification:
    2026.07.16
"""

# Importation des modules nécessaires
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QMainWindow

from dev.mod.saisie.UI.interface_principale import InterfacePrincipaleWidget
from dev.mod.saisie.UI.suivi_exterieur_window import SuiviExterieurWindow
from dev.backend import logger
from dev.backend.app_config import get_assets_path
from dev.core import session

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Configuration de la fenêtre
        self.setWindowIcon(QIcon(get_assets_path("imgs", "logo_snack.svg")))
        self.setWindowTitle("Morphoz SnackApp")
        self.setGeometry(100, 100, 1200, 800)

        self.interface_widget = InterfacePrincipaleWidget()
        self.setCentralWidget(self.interface_widget)

        # Initialiser les actions et les menus
        self.setup_shortcuts()
        self.setup_menus()

        # Fenêtre secondaire de suivi extérieur — créée à la première demande (lazy init)
        # pour éviter le crash Wayland zwp_text_input_v3 causé par deux surfaces au démarrage
        self._suivi_exterieur_window: SuiviExterieurWindow | None = None

        # Actions app depuis le volet de navigation
        self.interface_widget.action_app_demande.connect(self._on_action_app)

    def setup_shortcuts(self):
        """Configure les actions globales de la fenêtre."""

        self.quit_action = QAction("Quitter", self)
        self.quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_action.triggered.connect(lambda: session.gerer_fermeture(self))
        self.addAction(self.quit_action)

        self.fullscreen_action = QAction("Plein écran", self)
        self.fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(self.fullscreen_action)

        self.exit_fullscreen_action = QAction("Quitter le plein écran", self)
        self.exit_fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        self.exit_fullscreen_action.triggered.connect(self.exit_fullscreen)
        self.addAction(self.exit_fullscreen_action)

        self.minimize_action = QAction("Minimiser", self)
        self.minimize_action.setShortcut(QKeySequence("Ctrl+M"))
        self.minimize_action.triggered.connect(self.showMinimized)
        self.addAction(self.minimize_action)
    
    def setup_menus(self):
        """Remplacé par le volet de navigation tactile — masque la barre de menus."""
        self.menuBar().hide()
        
    
    def _on_action_app(self, action: str):
        """Gère les actions applicatives émises par le volet de navigation."""
        if action == "fullscreen":
            self.toggle_fullscreen()  # maj_etat_volet appelé en interne
        elif action == "quit":
            session.gerer_fermeture(self)
        elif action == "suivi_ext_toggle":
            est_visible = self._suivi_exterieur_window is not None and self._suivi_exterieur_window.isVisible()
            self._toggle_suivi_exterieur(not est_visible)
            self.interface_widget.maj_etat_volet("suivi_ext", not est_visible)

    def _toggle_suivi_exterieur(self, checked: bool):
        """Affiche ou masque la fenêtre de suivi extérieur."""
        if checked:
            if self._suivi_exterieur_window is None:
                self._suivi_exterieur_window = SuiviExterieurWindow()
                self._suivi_exterieur_window.closed.connect(
                    lambda: self.interface_widget.maj_etat_volet("suivi_ext", False)
                )
            self._suivi_exterieur_window.show()
            self._suivi_exterieur_window.raise_()
        elif self._suivi_exterieur_window is not None:
            self._suivi_exterieur_window.hide()
        logger.log(logger.AFFICHAGE_EXTERIEUR, {"etat": "activé" if checked else "désactivé"})

    def toggle_fullscreen(self):
        """Bascule le mode plein écran."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        self.interface_widget.maj_etat_volet("plein_ecran", self.isFullScreen())
    
    def exit_fullscreen(self):
        """Quitte le plein écran."""
        if self.isFullScreen():
            self.showNormal()
            self.interface_widget.maj_etat_volet("plein_ecran", False)

    def closeEvent(self, event):
        """Ferme l'affichage externe avant de fermer la fenêtre."""
        if self._suivi_exterieur_window is not None:
            self._suivi_exterieur_window.force_close()
        event.accept()
