#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window.py - Main Window Module

Description:
    This module contains the main window implementation for the Morphoz SnackApp UI.

Author :
    Dracudar

Version:
    2.4

Date de création :
    2026.05.12

Date de modification:
    2026.06.14
"""

# Importation des modules nécessaires
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from src.UI.view.interface_principale import InterfacePrincipaleWidget
from src.UI.suivi_exterieur_window import SuiviExterieurWindow
from src.backend import logger
from src.backend.update_checker import UpdateChecker
from src.core.version import APP_VERSION

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre
        self.setWindowIcon(QIcon("assets/imgs/logo_snack.svg"))
        self.setWindowTitle("Morphoz SnackApp")
        self.setGeometry(100, 100, 1200, 800)

        # Créer le widget central avec bannière de mise à jour
        self.interface_widget = InterfacePrincipaleWidget()
        self._update_banner = self._create_update_banner()

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(self._update_banner)
        container_layout.addWidget(self.interface_widget)
        self.setCentralWidget(container)

        # Initialiser les actions et les menus
        self.setup_shortcuts()
        self.setup_menus()

        # Fenêtre secondaire de suivi extérieur (créée une fois, masquée/affichée à la demande)
        self.suivi_exterieur_window = SuiviExterieurWindow()
        self.suivi_exterieur_window.closed.connect(
            lambda: self.interface_widget.maj_etat_volet("suivi_ext", False)
        )

        # Actions app depuis le volet de navigation
        self.interface_widget.action_app_demande.connect(self._on_action_app)
        
        # Vérification des mises à jour en arrière-plan
        self._update_checker = UpdateChecker(APP_VERSION, parent=self)
        self._update_checker.update_available.connect(self._show_update_banner)
        self._update_checker.start()
    
    def _create_update_banner(self) -> QFrame:
        """Crée la bannière de notification de mise à jour (masquée par défaut)."""
        frame = QFrame()
        frame.setObjectName("updateBanner")
        frame.setStyleSheet("""
            QFrame#updateBanner {
                background-color: #1e3a2f;
                border-bottom: 1px solid #2d6a4f;
            }
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 4, 8, 4)

        self._update_label = QLabel()
        self._update_label.setStyleSheet("color: #95d5b2; font-size: 12px;")
        layout.addWidget(self._update_label)
        layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setFlat(True)
        close_btn.setStyleSheet("color: #95d5b2; font-size: 11px; border: none;")
        close_btn.clicked.connect(frame.hide)
        layout.addWidget(close_btn)

        frame.hide()
        return frame

    def _show_update_banner(self, latest_version: str):
        """Affiche la bannière indiquant qu'une nouvelle version est disponible."""
        self._update_label.setText(
            f"Nouvelle version {latest_version} disponible — "
            "téléchargez-la depuis GitHub Releases."
        )
        self._update_banner.show()

    def setup_shortcuts(self):
        """Configure les actions globales de la fenêtre."""

        self.quit_action = QAction("Quitter", self)
        self.quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_action.triggered.connect(self.close)
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
            self.close()
        elif action == "suivi_ext_toggle":
            actif = not self.suivi_exterieur_window.isVisible()
            self._toggle_suivi_exterieur(actif)
            self.interface_widget.maj_etat_volet("suivi_ext", actif)

    def _toggle_suivi_exterieur(self, checked: bool):
        """Affiche ou masque la fenêtre de suivi extérieur."""
        if checked:
            self.suivi_exterieur_window.show()
            self.suivi_exterieur_window.raise_()
        else:
            self.suivi_exterieur_window.hide()
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
        """Ferme l'affichage externe avant de quitter l'application."""
        self.suivi_exterieur_window.force_close()
        event.accept()
