#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interface_principale.py - Vue principale de l'interface

Description:
    Assemble la saisie dynamique et le suivi des commandes dans la fenetre principale.

Author :
    Dracudar

Version:
    1.2

Date de création :
    2026.05.18

Date de modification:
    2026.06.10
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

# Pages affichées en mode split (saisie + suivi côte à côte) ; toutes les autres passent en plein écran.
_PAGES_MODE_SPLIT = frozenset({"saisie"})

from src.modules.carte.UI import CarteModule
from src.modules.commandes_historique.UI import CommandesHistoriqueModule
from src.modules.commandes_poste_preparation.UI.poste_preparation import PostePreparationModule
from src.modules.commandes_saisie.UI.commande_saisie import SaisieCommandeModule
from src.modules.commandes_suivi.UI.UI import SuiviCommandesModule
from src.modules.parametres.UI import ParametresModule
from src.modules.stock.UI import StockModule


class PlaceholderPage(QFrame):
    """Page générique affichant un titre et un message de substitution."""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setObjectName("placeholderPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        heading = QLabel(title)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet("color: #f5f5f5; font-size: 24px; font-weight: 700;")
        layout.addWidget(heading)

        body = QLabel(message)
        body.setWordWrap(True)
        body.setStyleSheet("color: #d6d6d6; font-size: 14px;")
        layout.addWidget(body)
        layout.addStretch()

        self.setStyleSheet(
            """
            QFrame#placeholderPage {
                background-color: #2f3136;
                border: 1px dashed #8a8a8a;
            }
            """
        )


class InterfacePrincipaleWidget(QWidget):
    """Assemble les zones principales de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        """Assemble le stack gauche (saisie, stock, carte, historique, paramètres) et le suivi à droite."""
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        self.left_stack = QStackedWidget()
        self.page_saisie = SaisieCommandeModule()
        self.page_stock = StockModule()
        self.page_carte = CarteModule()
        self.page_historique = CommandesHistoriqueModule()
        self.page_parametres = ParametresModule()
        self.page_poste_prep = PostePreparationModule()

        self.left_stack.addWidget(self.page_saisie)
        self.left_stack.addWidget(self.page_stock)
        self.left_stack.addWidget(self.page_carte)
        self.left_stack.addWidget(self.page_historique)
        self.left_stack.addWidget(self.page_parametres)
        self.left_stack.addWidget(self.page_poste_prep)

        self.suivi_module = SuiviCommandesModule()

        self.page_parametres.config_changed.connect(self.refresh_all_pages)
        self.page_parametres.go_back.connect(lambda: self.set_left_page("saisie"))
        self.page_historique.go_back.connect(lambda: self.set_left_page("saisie"))
        self.page_saisie.command_changed.connect(self.refresh_all_pages)

        root_layout.addWidget(self.left_stack, 2)
        root_layout.addWidget(self.suivi_module, 1)

        # Affiche les paramètres au démarrage
        self.set_left_page("parametres")

    def set_left_page(self, page_name: str):
        """Affiche la page demandée dans le stack gauche et adapte le mode d'affichage.

        Mode split (saisie + suivi côte à côte) pour « saisie », plein écran pour toutes les autres pages.

        :param page_name: Identifiant de la page (« saisie », « stock », « carte », « historique », « parametres »).
        """
        pages = {
            "saisie": self.page_saisie,
            "stock": self.page_stock,
            "carte": self.page_carte,
            "historique": self.page_historique,
            "parametres": self.page_parametres,
            "poste_preparation": self.page_poste_prep,
        }
        widget = pages.get(page_name)
        if widget is not None:
            self.left_stack.setCurrentWidget(widget)
            self._refresh_page(widget)
            self.suivi_module.setVisible(page_name in _PAGES_MODE_SPLIT)

    def refresh_all_pages(self):
        """Rafraîchit toutes les pages et le suivi (appelé sur changement de config ou de commande)."""
        self.page_saisie.refresh()
        self.page_stock.reload_from_disk()
        self.page_carte.reload_from_disk()
        self.page_historique.refresh_orders()
        self.page_poste_prep.refresh()
        self.suivi_module.tracker.refresh_orders()

    def _refresh_page(self, widget):
        """Appelle la méthode de rafraîchissement disponible sur le widget (refresh, reload_from_disk ou refresh_orders)."""
        if hasattr(widget, "refresh"):
            widget.refresh()
        elif hasattr(widget, "reload_from_disk"):
            widget.reload_from_disk()
        elif hasattr(widget, "refresh_orders"):
            widget.refresh_orders()
