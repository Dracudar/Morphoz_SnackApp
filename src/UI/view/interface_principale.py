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

from src.UI.modules.saisie_commande import SaisieCommandeModule
from src.UI.modules.suivi_commandes import SuiviCommandesModule


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
        self.page_stock = PlaceholderPage(
            "Module Stock",
            "Cette page accueillera le module de gestion du stock."
        )
        self.page_carte = PlaceholderPage(
            "Module Carte",
            "Cette page pourra servir a un second affichage pour dispatcher les commandes par type de plat."
        )
        self.page_parametres = PlaceholderPage(
            "Module Parametres",
            "Cette page accueillera les options de configuration."
        )

        self.left_stack.addWidget(self.page_saisie)
        self.left_stack.addWidget(self.page_stock)
        self.left_stack.addWidget(self.page_carte)
        self.left_stack.addWidget(self.page_parametres)

        self.suivi_module = SuiviCommandesModule()

        root_layout.addWidget(self.left_stack, 2)
        root_layout.addWidget(self.suivi_module, 1)

    def set_left_page(self, page_name: str):
        pages = {
            "saisie": self.page_saisie,
            "stock": self.page_stock,
            "carte": self.page_carte,
            "parametres": self.page_parametres,
        }
        widget = pages.get(page_name)
        if widget is not None:
            self.left_stack.setCurrentWidget(widget)
