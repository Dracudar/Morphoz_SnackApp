#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window_stats.py - Fenêtre principale de la vue Historique/Statistiques allégée

Description:
    Fenêtre principale de la vue allégée : statistiques de vente (avec export
    PDF), historique des commandes et journal des événements, sans saisie, ni
    stock, ni carte, ni impression. Barre de navigation tactile en haut (logo
    MegaSnack cliquable) et volet latéral dynamique en superposition (bascule
    Statistiques/Historique/Journal, plein écran, quitter). Le dossier data se
    choisit désormais uniquement depuis le launcher (accessible via le choix
    de fermeture "Revenir au launcher") : pas de page Paramètres tant qu'aucun
    réglage spécifique à ce mode n'existe. Démarre sur Statistiques, page
    d'accueil de ce mode.

Author :
    Dracudar

Version:
    1.3

Date de création :
    2026.07.05

Date de modification:
    2026.07.16
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QSize, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dev.backend.app_config import get_assets_path
from dev.core import session
from dev.mod.stats.UI.view.historique import HistoriqueConsultationModule
from dev.mod.stats.UI.view.logs import LogsModule
from dev.mod.stats.UI.view.stats import StatsModule
from dev.mod.saisie.UI.volet_navigation import OverlayFermeture
from dev.mod.stats.UI.panneau_lateral import VoletStats


class MainWindowStats(QMainWindow):
    """Fenêtre principale de la vue allégée Statistiques/Historique/Journal."""

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Morphoz SnackApp — Statistiques / Historique / Journal")
        self.setWindowIcon(QIcon(get_assets_path("imgs", "logo_snack.svg")))
        self.setGeometry(100, 100, 1200, 800)

        central = QWidget()
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_barre_nav())

        # Zone de contenu principale
        self._content_area = QWidget(central)
        content_layout = QHBoxLayout(self._content_area)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(0)

        self.left_stack = QStackedWidget()
        self.page_stats = StatsModule()
        self.page_historique = HistoriqueConsultationModule()
        self.page_logs = LogsModule()
        self.left_stack.addWidget(self.page_stats)
        self.left_stack.addWidget(self.page_historique)
        self.left_stack.addWidget(self.page_logs)
        content_layout.addWidget(self.left_stack)

        root_layout.addWidget(self._content_area, 1)

        # Overlay semi-transparent + volet en superposition sur _content_area
        self._overlay = OverlayFermeture(self._content_area)
        self._overlay.hide()
        self._overlay.clicked.connect(self._fermer_volet)

        self._volet = VoletStats(self._content_area)
        self._volet.page_demandee.connect(self.set_page)
        self._volet.action_app_demande.connect(self._on_action_app)
        self._volet.fermeture_demandee.connect(self._fermer_volet)
        self._volet.hide()

        # Le bouton "Retour" de chaque module ramène à l'accueil de cette vue (Statistiques)
        # (page_stats n'a pas de bouton "Retour" : c'est déjà la page d'accueil)
        self.page_historique.go_back.connect(lambda: self.set_page("stats"))
        self.page_logs.go_back.connect(lambda: self.set_page("stats"))

        # Repositionne overlay/volet lors des redimensionnements
        self._content_area.installEventFilter(self)

        self.setCentralWidget(central)
        self._setup_shortcuts()
        self.set_page("stats")

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

        logo_btn = QPushButton()
        logo_btn.setIcon(QIcon(get_assets_path("imgs", "MegaSnack.svg")))
        logo_btn.setIconSize(QSize(130, 28))
        logo_btn.setFixedSize(146, 44)
        logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logo_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; }"
            "QPushButton:hover { background-color: #2c2f33; }"
        )
        logo_btn.clicked.connect(self._basculer_volet)
        layout.addWidget(logo_btn)
        layout.addStretch(1)

        return barre

    def _setup_shortcuts(self):
        """Configure les raccourcis clavier globaux."""
        quit_action = QAction("Quitter", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(lambda: session.gerer_fermeture(self))
        self.addAction(quit_action)

        fs_action = QAction("Plein écran", self)
        fs_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        fs_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(fs_action)

        esc_action = QAction("Quitter plein écran", self)
        esc_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        esc_action.triggered.connect(self.exit_fullscreen)
        self.addAction(esc_action)

    # ── Navigation ────────────────────────────────────────────────────────────

    def set_page(self, page_id: str):
        """Affiche la page demandée (stats, historique ou logs) et rafraîchit son contenu."""
        pages = {
            "stats": self.page_stats,
            "historique": self.page_historique,
            "logs": self.page_logs,
        }
        widget = pages.get(page_id)
        if widget is None:
            return
        self.left_stack.setCurrentWidget(widget)
        self._volet.maj_page_active(page_id)
        if hasattr(widget, "refresh"):
            widget.refresh()
        elif hasattr(widget, "refresh_orders"):
            widget.refresh_orders()

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
            session.gerer_fermeture(self)

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
