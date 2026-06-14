#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interface_principale.py - Vue principale de l'interface

Description:
    Assemble la saisie dynamique et le suivi des commandes dans la fenetre principale.
    Inclut une barre de navigation tactile en haut et un volet latéral de navigation.

Author :
    Dracudar

Version:
    1.3

Date de création :
    2026.05.18

Date de modification:
    2026.06.13
"""

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

# Pages affichées en mode split (saisie + suivi côte à côte) ; toutes les autres passent en plein écran.
_PAGES_MODE_SPLIT = frozenset({"saisie"})

_NOMS_PAGES = {
    "saisie":            "Saisie commande",
    "stock":             "Stock",
    "carte":             "Carte",
    "historique":        "Historique",
    "logs":              "Journal",
    "parametres":        "Paramètres",
    "poste_preparation": "Poste de préparation",
}

from src.modules.carte.UI import CarteModule
from src.modules.commandes_historique.UI import CommandesHistoriqueModule
from src.modules.commandes_poste_preparation.UI.poste_preparation import PostePreparationModule
from src.modules.commandes_saisie.UI.commande_saisie import SaisieCommandeModule
from src.modules.commandes_suivi.UI.UI import SuiviCommandesModule
from src.modules.logs.UI import LogsModule
from src.modules.parametres.UI import ParametresModule
from src.modules.stock.UI import StockModule
from src.UI.view.volet_navigation import OverlayFermeture, VoletNavigation


class InterfacePrincipaleWidget(QWidget):
    """Assemble les zones principales de l'application avec barre de navigation tactile."""

    action_app_demande = Signal(str)  # "fullscreen" | "quit" | "suivi_ext_toggle"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Barre de navigation en haut (44 px)
        root.addWidget(self._build_barre_nav())

        # Zone de contenu principal
        self._content_area = QWidget(self)
        content_layout = QHBoxLayout(self._content_area)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        self.left_stack = QStackedWidget()
        self.page_saisie        = SaisieCommandeModule()
        self.page_stock         = StockModule()
        self.page_carte         = CarteModule()
        self.page_historique    = CommandesHistoriqueModule()
        self.page_logs          = LogsModule()
        self.page_parametres    = ParametresModule()
        self.page_poste_prep    = PostePreparationModule()

        self.left_stack.addWidget(self.page_saisie)
        self.left_stack.addWidget(self.page_stock)
        self.left_stack.addWidget(self.page_carte)
        self.left_stack.addWidget(self.page_historique)
        self.left_stack.addWidget(self.page_logs)
        self.left_stack.addWidget(self.page_parametres)
        self.left_stack.addWidget(self.page_poste_prep)

        self.suivi_module = SuiviCommandesModule()

        self.page_parametres.config_changed.connect(self.refresh_all_pages)
        self.page_parametres.go_back.connect(lambda: self.set_left_page("saisie"))
        self.page_parametres.go_to_poste_prep.connect(lambda: self.set_left_page("poste_preparation"))
        self.page_historique.go_back.connect(lambda: self.set_left_page("saisie"))
        self.page_logs.go_back.connect(lambda: self.set_left_page("saisie"))
        self.page_saisie.command_changed.connect(self.refresh_all_pages)

        content_layout.addWidget(self.left_stack, 2)
        content_layout.addWidget(self.suivi_module, 1)
        root.addWidget(self._content_area, 1)

        # Overlay et volet en superposition sur _content_area (hors layout)
        self._overlay = OverlayFermeture(self._content_area)
        self._overlay.hide()
        self._overlay.clicked.connect(self._fermer_volet)

        self._volet = VoletNavigation(self._content_area)
        self._volet.page_demandee.connect(self._on_nav_page)
        self._volet.action_app_demande.connect(self.action_app_demande)
        self._volet.hide()

        # Listener de redimensionnement sur _content_area pour repositionner l'overlay/volet
        self._content_area.installEventFilter(self)

        self.set_left_page("parametres")

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

        self._titre_page = QLabel("")
        self._titre_page.setStyleSheet(
            "color: #d6d6d6; font-size: 14px; font-weight: 600; padding-left: 4px;"
        )
        layout.addWidget(self._titre_page, 1)

        return barre

    # ── Navigation ────────────────────────────────────────────────────────────

    def set_left_page(self, page_name: str):
        """Affiche la page demandée et adapte le mode d'affichage (split / plein écran)."""
        pages = {
            "saisie":            self.page_saisie,
            "stock":             self.page_stock,
            "carte":             self.page_carte,
            "historique":        self.page_historique,
            "logs":              self.page_logs,
            "parametres":        self.page_parametres,
            "poste_preparation": self.page_poste_prep,
        }
        widget = pages.get(page_name)
        if widget is not None:
            self.left_stack.setCurrentWidget(widget)
            self._refresh_page(widget)
            self.suivi_module.setVisible(page_name in _PAGES_MODE_SPLIT)
            self._titre_page.setText(_NOMS_PAGES.get(page_name, ""))

    def refresh_all_pages(self):
        """Rafraîchit toutes les pages et le suivi."""
        self.page_saisie.refresh()
        self.page_stock.refresh()
        self.page_carte.reload_from_disk()
        self.page_historique.refresh_orders()
        self.page_poste_prep.refresh()
        self.suivi_module.tracker.refresh_orders()

    def _refresh_page(self, widget):
        if hasattr(widget, "refresh"):
            widget.refresh()
        elif hasattr(widget, "reload_from_disk"):
            widget.reload_from_disk()
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
        self._volet.setGeometry(0, 0, 240, h)
        self._overlay.show()
        self._overlay.raise_()
        self._volet.show()
        self._volet.raise_()

    def _fermer_volet(self):
        self._volet.hide()
        self._overlay.hide()

    def _on_nav_page(self, page_id: str):
        self.set_left_page(page_id)
        self._fermer_volet()  # ferme aussi l'overlay (le volet se cache lui-même en parallèle)

    def maj_etat_volet(self, cle: str, actif: bool):
        """Mise à jour d'un état dans le volet (plein_ecran, suivi_ext)."""
        if cle == "plein_ecran":
            self._volet.maj_etat_plein_ecran(actif)
        elif cle == "suivi_ext":
            self._volet.maj_etat_suivi_ext(actif)

    # ── Événements ────────────────────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self._content_area and event.type() == QEvent.Type.Resize:
            w = self._content_area.width()
            h = self._content_area.height()
            self._overlay.setGeometry(0, 0, w, h)
            self._volet.setGeometry(0, 0, 240, h)
        return False
