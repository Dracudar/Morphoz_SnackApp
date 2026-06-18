#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window_prep.py - Fenêtre principale du poste de préparation allégé

Description:
    Fenêtre principale de l'application légère pour les postes de préparation.
    Barre de navigation tactile en haut (logo MegaSnack + bouton hamburger) et
    volet latéral dynamique en superposition pour les paramètres (dossier data,
    plein écran, quitter).

Author :
    Dracudar

Version:
    2.0

Date de création :
    2026.06.14

Date de modification:
    2026.06.14
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.backend.app_config import get_assets_path
from src.modules.commandes_poste_preparation.UI.poste_preparation import PostePreparationModule
from src.UI.view.volet_navigation import OverlayFermeture
from src.UI_prep.panneau_lateral import VoletPrep


class MainWindowPrep(QMainWindow):
    """Fenêtre principale du poste de préparation allégé."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Morphoz SnackApp — Poste de préparation")
        self.setWindowIcon(QIcon(get_assets_path("imgs", "logo_snack.svg")))
        self.setGeometry(100, 100, 1200, 800)

        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_barre_nav())

        # Zone de contenu principale (PostePreparationModule plein écran)
        self._content_area = QWidget(central)
        content_layout = QHBoxLayout(self._content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._poste = PostePreparationModule()
        content_layout.addWidget(self._poste)

        root_layout.addWidget(self._content_area, 1)

        # Overlay semi-transparent + volet en superposition sur _content_area
        self._overlay = OverlayFermeture(self._content_area)
        self._overlay.hide()
        self._overlay.clicked.connect(self._fermer_volet)

        self._volet = VoletPrep(self._content_area)
        self._volet.action_app_demande.connect(self._on_action_app)
        self._volet.dossier_applique.connect(self._poste.refresh)
        self._volet.hide()

        # Repositionne overlay/volet lors des redimensionnements
        self._content_area.installEventFilter(self)

        self.setCentralWidget(central)
        self._setup_shortcuts()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_barre_nav(self) -> QFrame:
        barre = QFrame()
        barre.setObjectName("barreNavigation")
        barre.setFixedHeight(44)
        barre.setStyleSheet(
            "QFrame#barreNavigation {"
            "  background-color: #23272a;"
            "  border-bottom: 1px solid #36393f;"
            "}"
        )
        layout = QHBoxLayout(barre)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(0)

        btn_menu = QPushButton("☰")
        btn_menu.setFixedSize(52, 44)
        btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_menu.setStyleSheet(
            "QPushButton { color: #d6d6d6; background: transparent; border: none; font-size: 20px; }"
            "QPushButton:hover { color: #f5f5f5; background-color: #2c2f33; }"
        )
        btn_menu.clicked.connect(self._basculer_volet)
        layout.addWidget(btn_menu)

        logo = QSvgWidget(get_assets_path("imgs", "MegaSnack.svg"))
        logo.setFixedSize(130, 28)
        layout.addWidget(logo)
        layout.addStretch(1)

        return barre

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

    # ── Volet ─────────────────────────────────────────────────────────────────

    def _basculer_volet(self):
        if self._volet.isVisible():
            self._fermer_volet()
        else:
            self._ouvrir_volet()

    def _ouvrir_volet(self):
        w = self._content_area.width()
        h = self._content_area.height()
        self._overlay.setGeometry(0, 0, w, h)
        self._volet.setGeometry(0, 0, 260, h)
        self._overlay.show()
        self._overlay.raise_()
        self._volet.show()
        self._volet.raise_()

    def _fermer_volet(self):
        self._volet.hide()
        self._overlay.hide()

    def _on_action_app(self, action: str):
        """Gère les actions émises par le volet."""
        if action == "fullscreen":
            self.toggle_fullscreen()
        elif action == "quit":
            self.close()

    # ── Événements ────────────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self._content_area and event.type() == QEvent.Type.Resize:
            w = self._content_area.width()
            h = self._content_area.height()
            self._overlay.setGeometry(0, 0, w, h)
            self._volet.setGeometry(0, 0, 260, h)
        return False

    # ── Plein écran ───────────────────────────────────────────────────────────

    def toggle_fullscreen(self):
        """Bascule le mode plein écran."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
        self._volet.maj_etat_plein_ecran(self.isFullScreen())

    def exit_fullscreen(self):
        """Quitte le mode plein écran si actif."""
        if self.isFullScreen():
            self.showNormal()
            self._volet.maj_etat_plein_ecran(False)
