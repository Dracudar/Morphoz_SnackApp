#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interface_principale.py - Vue principale de l'interface

Description:
    Assemble la saisie dynamique et le suivi des commandes dans la fenetre principale.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.18

Date de modification:
    2026.05.18
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from src.UI.modules.carte import CarteModule
from src.UI.modules.commande_saisie import SaisieCommandeModule
from src.UI.modules.commandes_historique import CommandesHistoriqueModule
from src.UI.modules.commandes_suivi import SuiviCommandesModule
from src.UI.modules.parametres import ParametresModule
from src.UI.modules.stock import StockModule


class PlaceholderPage(QFrame):
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
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(8)

        self.left_stack = QStackedWidget()
        self.page_saisie = SaisieCommandeModule()
        self.page_stock = StockModule()
        self.page_carte = CarteModule()
        self.page_historique = CommandesHistoriqueModule()
        self.page_parametres = ParametresModule()

        self.left_stack.addWidget(self.page_saisie)
        self.left_stack.addWidget(self.page_stock)
        self.left_stack.addWidget(self.page_carte)
        self.left_stack.addWidget(self.page_historique)
        self.left_stack.addWidget(self.page_parametres)

        self.suivi_module = SuiviCommandesModule()

        self.page_parametres.config_changed.connect(self.refresh_all_pages)
        self.page_saisie.command_changed.connect(self.refresh_all_pages)

        root_layout.addWidget(self.left_stack, 2)
        root_layout.addWidget(self.suivi_module, 1)

    def set_left_page(self, page_name: str):
        pages = {
            "saisie": self.page_saisie,
            "stock": self.page_stock,
            "carte": self.page_carte,
            "historique": self.page_historique,
            "parametres": self.page_parametres,
        }
        widget = pages.get(page_name)
        if widget is not None:
            self.left_stack.setCurrentWidget(widget)
            self._refresh_page(widget)

    def refresh_all_pages(self):
        self.page_saisie.refresh()
        self.page_stock.reload_from_disk()
        self.page_carte.reload_from_disk()
        self.page_historique.refresh_orders()
        self.suivi_module.tracker.refresh_orders()

    def _refresh_page(self, widget):
        if hasattr(widget, "refresh"):
            widget.refresh()
        elif hasattr(widget, "reload_from_disk"):
            widget.reload_from_disk()
        elif hasattr(widget, "refresh_orders"):
            widget.refresh_orders()
