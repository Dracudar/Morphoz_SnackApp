#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
commande_saisie.py

Description:
    Interface Qt/PySide6 de saisie des commandes : menu par catégories de plats, liste de la commande en cours, total et actions (annuler/valider avec dialogue de paiement).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.18

Date de modification:
    2026.06.04
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer, Signal
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

from src.backend.data_sources import get_draft_orders, get_menu_categories
from src.backend.app_config import get_archive_folder_path, get_logs_folder_path
from src.modules.commandes_saisie.UI.widgets.bouton_menu import BoutonMenu
from src.modules.commandes_saisie.UI.widgets.item_row import ItemRow, extract_plat_sort_key
from src.modules.commandes_saisie.UI.payment_dialog import PaymentDialog
from src.modules.commandes_saisie.utils.plats_router import route_plat_selection
from src.modules.commandes_saisie.backend.saver import MAJ_commande
from src.modules.commandes_saisie.backend.gestion import (
    annuler_plat,
    annuler_all_plats
)
from src.modules.commandes_saisie.backend.paiements import (
    paiement_carte,
    paiement_especes,
    gratuit,
)


class SaisieCommandeModule(QFrame):
    """Module de saisie des commandes : menu par catégories, liste des articles et actions."""

    command_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("saisieCommandeModule")
        self.refresh_timer = None
        self._build_ui()
        self._setup_refresh_timer()
        self.refresh()

    def _build_ui(self):
        """Construit la mise en page principale : cadre menu (35 %) et cadre détail commande (65 %)."""
        self.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # ========== Menu Frame (35% height) ==========
        self._build_menu_frame(main_layout)

        # ========== Command Detail Frame (65% height) ==========
        self._build_command_detail_frame(main_layout)

        # Stylesheet
        self._apply_stylesheets()

    def _build_menu_frame(self, parent_layout):
        """Construit le cadre menu avec sa grille de boutons de catégories."""
        self.menu_frame = QFrame()
        self.menu_frame.setObjectName("menuFrame")
        menu_layout = QVBoxLayout(self.menu_frame)
        menu_layout.setContentsMargins(10, 10, 10, 10)
        menu_layout.setSpacing(10)

        # Title
        menu_title = QLabel("Menu")
        menu_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        menu_title.setObjectName("sectionTitle")
        menu_layout.addWidget(menu_title)

        # Scrollable menu grid
        self.menu_scroll = QScrollArea()
        self.menu_scroll.setWidgetResizable(True)
        self.menu_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.menu_scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.menu_scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget > QWidget { background-color: #2f3136; }"
        )

        self.menu_container = QWidget()
        self.menu_grid = QGridLayout(self.menu_container)
        self.menu_grid.setContentsMargins(0, 0, 0, 0)
        self.menu_grid.setHorizontalSpacing(8)
        self.menu_grid.setVerticalSpacing(8)
        self.menu_scroll.setWidget(self.menu_container)
        menu_layout.addWidget(self.menu_scroll)

        parent_layout.addWidget(self.menu_frame, 0)

    def _build_command_detail_frame(self, parent_layout):
        """Construit le cadre détail commande en 4 sections : titre, liste articles, montant, actions."""
        detail_frame = QFrame()
        detail_frame.setObjectName("detailFrame")
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(10, 10, 10, 10)
        detail_layout.setSpacing(10)

        # Section 1: Title (4%)
        self.title_label = QLabel("Aucune commande en cours")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("sectionTitle")
        detail_layout.addWidget(self.title_label)

        # Section 2: Items List (34%)
        self._build_items_section(detail_layout)

        # Section 3: Amount Display (3%)
        self.amount_label = QLabel("Total: 0.00 €")
        self.amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.amount_label.setObjectName("amountLabel")
        detail_layout.addWidget(self.amount_label)

        # Section 4: Action Buttons (4%)
        self._build_actions_section(detail_layout)

        # Status message label (feedback)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #a8d08d; font-size: 13px; font-weight: 600;")
        detail_layout.addWidget(self.status_label)

        parent_layout.addWidget(detail_frame, 1)

    def _build_items_section(self, parent_layout):
        """Construit la zone scrollable qui contient les lignes d'articles."""
        items_scroll = QScrollArea()
        items_scroll.setWidgetResizable(True)
        items_scroll.setFrameShape(QFrame.Shape.NoFrame)
        items_scroll.setStyleSheet(
            "QScrollArea, QScrollArea > QWidget > QWidget { background-color: #2f3136; }"
        )

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.addStretch()

        items_scroll.setWidget(self.items_container)
        parent_layout.addWidget(items_scroll, 1)

    def _build_actions_section(self, parent_layout):
        """Construit la section des boutons d'action (Annuler commande / Valider)."""
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.button_cancel = QPushButton("Annuler commande")
        self.button_cancel.setObjectName("actionButton")
        self.button_cancel.setEnabled(False)

        self.button_validate = QPushButton("Valider")
        self.button_validate.setObjectName("actionButton")
        self.button_validate.setEnabled(False)

        self.button_cancel.clicked.connect(self._handle_cancel_command)
        self.button_validate.clicked.connect(self._handle_validate_command)

        actions_layout.addWidget(self.button_cancel)
        actions_layout.addWidget(self.button_validate, 1)

        parent_layout.addLayout(actions_layout)

    def _apply_stylesheets(self):
        """Applique les feuilles de style du module."""
        self.setStyleSheet(
            """
            QFrame#saisieCommandeModule {
                background-color: #2f3136;
                border: none;
            }
            QFrame#menuFrame, QFrame#detailFrame {
                background-color: #2f3136;
                border: 1px solid #7f7f7f;
            }
            QLabel#sectionTitle {
                color: #f5f5f5;
                font-size: 22px;
                font-weight: 700;
                padding: 4px;
            }
            QLabel#amountLabel {
                color: #f5f5f5;
                font-size: 16px;
                font-weight: 700;
                padding: 8px;
                background-color: #3a3d43;
                border-radius: 4px;
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

    # ==================== Data Retrieval Methods ====================

    def _get_current_order(self) -> Optional[Dict]:
        """Retourne la première commande en brouillon active, ou None s'il n'y en a pas."""
        orders = get_draft_orders()
        return orders[0] if orders else None

    def _get_current_order_path(self) -> Optional[Path]:
        """Retourne le chemin du fichier JSON de la commande en cours, ou None."""
        order = self._get_current_order()
        return order["file"] if order else None

    # ==================== State Display Methods ====================

    def _display_no_order_state(self):
        """Affiche l'état « aucune commande en cours » : titre vide, liste vide, boutons désactivés."""
        self.title_label.setText("Aucune commande en cours")
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.items_layout.addStretch()
        self.amount_label.setText("Total: 0.00 €")
        self.button_cancel.setEnabled(False)
        self.button_validate.setEnabled(False)

    def _display_order_state(self, order: Dict):
        """Affiche l'état d'une commande active : titre, articles, montant et boutons activés."""
        self.title_label.setText(f"Commande {order['id']}")
        self._refresh_items_display(order)
        self._update_total_display(order)
        self.button_cancel.setEnabled(True)
        # Update validate button with amount
        amount = order.get("amount", 0)
        self.button_validate.setText(f"Valider ({amount:.2f} €)")
        self.button_validate.setEnabled(True)

    def _refresh_items_display(self, order: Dict):
        """Reconstruit la liste des articles à partir de la commande active."""
        # Clear existing items
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add ItemRow for each item, sorted by sequence number
        items = sorted(order.get("items", []), key=lambda x: extract_plat_sort_key(x.get("id", "")))
        for item_data in items:
            row = ItemRow(item_data["id"], item_data)
            row.item_cancelled.connect(self._handle_item_cancel)
            self.items_layout.addWidget(row)

        self.items_layout.addStretch()

    def _update_total_display(self, order: Dict):
        """Met à jour l'étiquette du montant total."""
        amount = order.get("amount", 0)
        self.amount_label.setText(f"Total: {amount:.2f} €")

    # ==================== Event Handlers ====================

    def _handle_item_cancel(self, item_id: str):
        """Annule un article de la commande en cours et rafraîchit l'affichage."""
        order_path = self._get_current_order_path()
        if not order_path:
            self.status_label.setText("Erreur: Aucune commande")
            return

        try:
            annuler_plat(str(order_path), item_id)
            self.status_label.setText(f"Item {item_id} annulé")
            self.refresh()
            self.command_changed.emit()
        except Exception as e:
            self.status_label.setText(f"Erreur annulation: {str(e)}")

    def _handle_cancel_command(self):
        """Annule l'intégralité de la commande en cours et rafraîchit l'affichage."""
        order_path = self._get_current_order_path()
        if not order_path:
            self.status_label.setText("Erreur: Aucune commande")
            return

        try:
            annuler_all_plats(str(order_path))
            self.status_label.setText("Commande annulée")
            self.refresh()
            self.command_changed.emit()
        except Exception as e:
            self.status_label.setText(f"Erreur annulation: {str(e)}")

    def _handle_validate_command(self):
        """Ouvre le dialogue de paiement pour valider la commande en cours."""
        order = self._get_current_order()
        if not order:
            self.status_label.setText("Erreur: Aucune commande")
            return

        # Show payment dialog
        dialog = PaymentDialog(order.get("amount", 0), parent=self)
        dialog.payment_selected.connect(self._process_payment)
        dialog.exec()

    def _process_payment(self, payment_type: str):
        """Traite le mode de paiement sélectionné et déclenche la validation de la commande."""
        order_path = self._get_current_order_path()
        if not order_path:
            return

        try:
            if payment_type == "Carte":
                paiement_carte(str(order_path))
                msg = "Paiement carte effectué ✓"
            elif payment_type == "Espèces":
                paiement_especes(str(order_path))
                msg = "Paiement espèces effectué ✓"
            elif payment_type == "Gratuit":
                gratuit(str(order_path))
                msg = "Repas gratuit enregistré ✓"
            else:
                msg = "Mode de paiement inconnu"

            self.status_label.setText(msg)
            self.refresh()
            self.command_changed.emit()
        except Exception as e:
            self.status_label.setText(f"Erreur paiement: {str(e)}")

    # ==================== Menu Building & Refresh ====================

    def refresh(self):
        """Rafraîchit le menu et l'état de la commande — appelé par le timer ou en externe."""
        self.refresh_menu()
        order = self._get_current_order()
        if order:
            self._display_order_state(order)
        else:
            self._display_no_order_state()

    def refresh_menu(self):
        """Reconstruit les boutons du menu à partir de la carte JSON."""
        # Clear existing buttons
        while self.menu_grid.count():
            item = self.menu_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        categories = get_menu_categories()
        visible_categories = [cat for cat in categories if not cat.get("hidden", False)]

        if not visible_categories:
            placeholder = QLabel("Aucune categorie trouvee.")
            placeholder.setStyleSheet("color: #d6d6d6; font-size: 14px;")
            self.menu_grid.addWidget(placeholder, 0, 0)
            self.menu_scroll.setFixedHeight(118)
            return

        columns = 5
        for index, category in enumerate(visible_categories):
            label = category["name"]
            icon_path = category.get("icon_path")
            button = BoutonMenu(label, svg_path=icon_path)

            # Disable if not enabled
            if not category.get("enabled", True):
                button.setEnabled(False)
                button.setToolTip("Categorie indisponible")
            else:
                button.clicked.connect(
                    lambda _checked=False, cat=category: self._on_category_button_clicked(cat["name"])
                )

            row = index // columns
            column = index % columns
            self.menu_grid.addWidget(button, row, column)

        # Adjust scroll height
        row_count = ((len(visible_categories) - 1) // columns) + 1
        scroll_height = min(240, max(118, 24 + (row_count * 128)))
        self.menu_scroll.setFixedHeight(scroll_height)

    def _on_category_button_clicked(self, category_name: str):
        """Gère le clic sur un bouton de catégorie : route vers le handler du plat correspondant."""
        order_path = self._get_current_order_path()

        # Route to plat handler (opens UI or adds directly)
        result = route_plat_selection(
            category_name,
            context=None,
            command_path=str(order_path) if order_path else "",
        )

        if result:
            # Get archive paths for saving
            commandes_path = str(get_archive_folder_path())
            logs_path = str(get_logs_folder_path())

            # Add result to order using MAJ_commande()
            MAJ_commande(commandes_path, logs_path, result)
            self.refresh()
            self.command_changed.emit()

    # ==================== Auto-Refresh Timer ====================

    def _setup_refresh_timer(self):
        """Démarre le timer de rafraîchissement automatique (intervalle : 2 secondes)."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(2000)
        self.refresh_timer.timeout.connect(self._on_timer_tick)
        self.refresh_timer.start()

    def _on_timer_tick(self):
        """Appelé toutes les 2 secondes : met à jour la liste et le montant si une commande est active."""
        order = self._get_current_order()
        if order:
            self._refresh_items_display(order)
            self._update_total_display(order)
        else:
            self._display_no_order_state()
