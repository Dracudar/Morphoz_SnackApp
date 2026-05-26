#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
saisie_commande.py - Module de saisie des commandes

Description:
    Bloc principal de gauche avec boutons de carte dynamiques,
    detail de commande et actions de validation.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.18

Date de modification:
    2026.05.18
"""

from __future__ import annotations

import unicodedata

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.UI.utils.data_sources import get_live_orders, get_menu_categories
from src.UI.utils.module_registry import discover_module_registry
from src.UI.widgets.bouton_menu import BoutonMenu


class SaisieCommandeModule(QFrame):
    """Bloc de saisie dynamique de la commande en cours."""

    command_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("saisieCommandeModule")
        self.selected_category = None
        self._cancel_handler = None
        self._validate_handler = None
        self._pay_handler = None
        self._module_registry = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.menu_frame = QFrame()
        self.menu_frame.setObjectName("menuFrame")
        menu_layout = QVBoxLayout(self.menu_frame)
        menu_layout.setContentsMargins(10, 10, 10, 10)
        menu_layout.setSpacing(10)

        menu_title = QLabel("Menu")
        menu_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        menu_title.setObjectName("sectionTitle")
        menu_layout.addWidget(menu_title)

        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.menu_scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.menu_scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background-color: #2f3136; }")

        self.menu_container = QWidget()
        self.menu_grid = QGridLayout(self.menu_container)
        self.menu_grid.setContentsMargins(0, 0, 0, 0)
        self.menu_grid.setHorizontalSpacing(8)
        self.menu_grid.setVerticalSpacing(8)
        self.menu_scroll.setWidget(self.menu_container)
        menu_layout.addWidget(self.menu_scroll)

        self.command_summary = QLabel("Commandes actives : 0 | Plats en attente : 0")
        self.command_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.command_summary.setObjectName("summaryLabel")
        self.command_summary.setWordWrap(True)
        menu_layout.addWidget(self.command_summary)

        main_layout.addWidget(self.menu_frame, 0)

        detail_frame = QFrame()
        detail_frame.setObjectName("detailFrame")
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(10, 10, 10, 10)
        detail_layout.setSpacing(10)

        self.detail_title = QLabel("Aucune commande en cours...")
        self.detail_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_title.setObjectName("sectionTitle")
        detail_layout.addWidget(self.detail_title)

        self.detail_summary = QLabel(
            "Selectionne un type de plat pour afficher ses informations.\n"
            "Cette zone accueillera ensuite le module de personnalisation correspondant."
        )
        self.detail_summary.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.detail_summary.setWordWrap(True)
        self.detail_summary.setStyleSheet("color: #d6d6d6; font-size: 14px;")
        detail_layout.addWidget(self.detail_summary)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #a8d08d; font-size: 13px; font-weight: 600;")
        detail_layout.addWidget(self.status_label)

        detail_layout.addStretch()

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setObjectName("actionButton")
        self.validate_button = QPushButton("Valider")
        self.validate_button.setObjectName("actionButton")
        self.pay_button = QPushButton("Paiement")
        self.pay_button.setObjectName("actionButton")

        self.cancel_button.clicked.connect(self._trigger_cancel)
        self.validate_button.clicked.connect(self._trigger_validate)
        self.pay_button.clicked.connect(self._trigger_pay)

        actions_layout.addWidget(self.cancel_button)
        actions_layout.addWidget(self.validate_button)
        actions_layout.addWidget(self.pay_button)
        detail_layout.addLayout(actions_layout)

        main_layout.addWidget(detail_frame, 1)

        self.setStyleSheet(
            """
            QFrame#saisieCommandeModule {
                background-color: #2f3136;
                border: 1px solid #7f7f7f;
            }
            QFrame#menuFrame, QFrame#detailFrame {
                background-color: #2f3136;
                border: 1px solid #7f7f7f;
            }
            QLabel#summaryLabel {
                color: #d6d6d6;
                font-size: 13px;
                font-weight: 600;
                padding: 2px 6px;
            }
            QLabel#sectionTitle {
                color: #f5f5f5;
                font-size: 22px;
                font-weight: 700;
                padding: 4px;
            }
            QPushButton#actionButton {
                background-color: #4f545e;
                border: 1px solid #7d8390;
                border-radius: 7px;
                color: #f5f5f5;
                font-size: 14px;
                font-weight: 700;
                min-height: 40px;
                padding: 6px 12px;
            }
            QPushButton#actionButton:hover {
                background-color: #626978;
            }
            QPushButton#actionButton:disabled {
                color: #8f949c;
                background-color: #3a3d43;
                border-color: #595d64;
            }
            """
        )

    def refresh(self):
        self._module_registry = discover_module_registry()
        self.refresh_menu()
        self.refresh_live_summary()

    def set_action_handlers(self, cancel_handler=None, validate_handler=None, pay_handler=None):
        self._cancel_handler = cancel_handler
        self._validate_handler = validate_handler
        self._pay_handler = pay_handler
        self._update_action_state()

    def _update_action_state(self):
        self.cancel_button.setEnabled(callable(self._cancel_handler))
        self.validate_button.setEnabled(callable(self._validate_handler))
        self.pay_button.setEnabled(callable(self._pay_handler))

    def refresh_menu(self):
        """Reconstruit les boutons depuis la carte JSON."""
        while self.menu_grid.count():
            item = self.menu_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        categories = get_menu_categories()
        visible_categories = [category for category in categories if not category.get("hidden", False)]

        if not visible_categories:
            placeholder = QLabel("Aucune categorie trouvee dans la carte.")
            placeholder.setStyleSheet("color: #d6d6d6; font-size: 14px;")
            self.menu_grid.addWidget(placeholder, 0, 0)
            self.menu_scroll.setFixedHeight(118)
            self.selected_category = None
            self._update_action_state()
            return

        columns = 5
        for index, category in enumerate(visible_categories):
            label = category["name"]
            module_entry = self._module_registry.get(self._normalized_key(label))
            icon_path = module_entry.get("icon_path") if module_entry else category.get("icon_path")
            button = BoutonMenu(label, icon_path=icon_path)

            if module_entry and not module_entry.get("enabled", True):
                button.setEnabled(False)
                tooltip = module_entry.get("tooltip") or "Module desactive"
                button.setToolTip(str(tooltip))
            elif not category.get("enabled", True):
                button.setEnabled(False)
                if category.get("hidden", False):
                    button.setToolTip("Categorie retiree de la carte")
                else:
                    button.setToolTip("Categorie temporairement indisponible")
            else:
                if module_entry and callable(module_entry.get("action")):
                    button.clicked.connect(
                        lambda _checked=False, entry=module_entry, data=category: self._execute_module_action(entry, data)
                    )
                else:
                    button.clicked.connect(lambda _checked=False, data=category: self.select_category(data))
            row = index // columns
            column = index % columns
            self.menu_grid.addWidget(button, row, column)

        row_count = ((len(visible_categories) - 1) // columns) + 1
        scroll_height = min(240, max(118, 24 + (row_count * 104)))
        self.menu_scroll.setFixedHeight(scroll_height)

    def refresh_live_summary(self):
        orders = get_live_orders()
        total_orders = len(orders)
        total_pending_items = sum(order.get("pending_count", 0) for order in orders)
        self.command_summary.setText(
            f"Commandes actives : {total_orders} | Plats en attente : {total_pending_items}"
        )

    def select_category(self, category):
        self.selected_category = category
        self.detail_title.setText(category["name"])

        price = category.get("price")
        recipe_count = category.get("recipe_count", 0)
        state = category.get("state", "")
        availability = "Disponible" if category.get("enabled", True) else "Indisponible"
        details = [f"Etat: {state}"]
        details.append(f"Disponibilite: {availability}")
        if price is not None:
            details.append(f"Prix: {price:.2f} EUR")
        if recipe_count:
            details.append(f"Recettes: {recipe_count}")

        self.detail_summary.setText("\n".join(details))
        self._update_action_state()

    def _normalized_key(self, value: str) -> str:
        ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        return "".join(character for character in ascii_text.lower() if character.isalnum())

    def _execute_module_action(self, module_entry, category):
        action = module_entry.get("action")
        if not callable(action):
            self.status_label.setText("Aucune action disponible pour ce module.")
            return

        result = action(self)
        if isinstance(result, dict):
            self.status_label.setText(result.get("message", "Action executee."))
        else:
            self.status_label.setText("Action executee.")

        self.refresh_live_summary()
        self.command_changed.emit()

    def _trigger_cancel(self):
        if callable(self._cancel_handler):
            self._cancel_handler(self.selected_category)

    def _trigger_validate(self):
        if callable(self._validate_handler):
            self._validate_handler(self.selected_category)

    def _trigger_pay(self):
        if callable(self._pay_handler):
            self._pay_handler(self.selected_category)
