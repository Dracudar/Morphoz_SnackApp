#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
commande_saisie.py

Description:
    Interface Qt/PySide6 de saisie des commandes : menu par catégories de plats, liste de la commande en cours, total et actions (annuler/valider avec dialogue de paiement).

Author :
    Dracudar

Version:
    1.5

Date de création :
    2026.05.18

Date de modification:
    2026.06.15
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QEvent, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.utils.tactile import ScrollAreaTactile
from src.backend.data.categories import get_menu_categories
from src.backend.data.commandes import get_draft_orders
from src.backend.config.chemins import get_archive_folder_path, get_logs_folder_path
from src.UI.saisie.widgets.bouton_menu import BoutonMenu
from src.UI.saisie.widgets.item_row import ItemRow, extract_plat_sort_key
from src.UI.saisie.payment_dialog import PaymentDialog
from src.UI.saisie.utils.plats_router import route_plat_selection, check_disponibilite_plat
from src.backend.saisie.saver import MAJ_commande
from src.backend.saisie.gestion import (
    annuler_plat,
    annuler_all_plats,
    set_prioritaire,
)
def _make_cancel_icon(size: int = 26) -> QIcon:
    """Charge cancel.svg et retourne un QIcon avec modes normal (blanc) et désactivé (gris)."""
    def _colorize(color: str) -> QPixmap:
        renderer = QSvgRenderer("assets/icons/cancel.svg")
        raw = QPixmap(size, size)
        raw.fill(Qt.transparent)
        p = QPainter(raw)
        renderer.render(p)
        p.end()
        result = QPixmap(size, size)
        result.fill(Qt.transparent)
        p2 = QPainter(result)
        p2.drawPixmap(0, 0, raw)
        p2.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p2.fillRect(result.rect(), QColor(color))
        p2.end()
        return result

    icon = QIcon()
    icon.addPixmap(_colorize("white"), QIcon.Mode.Normal)
    icon.addPixmap(_colorize("#595d64"), QIcon.Mode.Disabled)
    return icon


from src.backend.saisie.paiements import (
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
        self.menu_scroll = ScrollAreaTactile()
        # widgetResizable=False : le conteneur garde sa taille naturelle (pas d'étirement)
        # AlignHCenter : Qt centre le conteneur quand il est plus étroit que le viewport
        self.menu_scroll.setWidgetResizable(False)
        self.menu_scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.menu_scroll.viewport().installEventFilter(self)

        self.menu_container = QWidget()
        self.menu_grid = QGridLayout(self.menu_container)
        self.menu_grid.setContentsMargins(0, 0, 0, 0)
        self.menu_grid.setHorizontalSpacing(8)
        self.menu_grid.setVerticalSpacing(8)
        self.menu_scroll.setWidget(self.menu_container)
        menu_layout.addWidget(self.menu_scroll)

        self._menu_button_widgets: list[BoutonMenu] = []
        self._current_menu_columns: int = 0

        parent_layout.addWidget(self.menu_frame, 0)

    def _build_command_detail_frame(self, parent_layout):
        """Construit le cadre détail commande en 3 sections : titre, liste articles, actions."""
        detail_frame = QFrame()
        detail_frame.setObjectName("detailFrame")
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(10, 10, 10, 10)
        detail_layout.setSpacing(10)

        # Section 1: Title
        self.title_label = QLabel("Aucune commande en cours")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("sectionTitle")
        detail_layout.addWidget(self.title_label)

        # Section 2: Items List
        self._build_items_section(detail_layout)

        # Section 3: Action Buttons
        self._build_actions_section(detail_layout)

        # Status message label (feedback)
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #a8d08d; font-size: 13px; font-weight: 600;")
        detail_layout.addWidget(self.status_label)

        parent_layout.addWidget(detail_frame, 1)

    def _build_items_section(self, parent_layout):
        """Construit la zone scrollable qui contient les lignes d'articles."""
        items_scroll = ScrollAreaTactile()

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.addStretch()

        items_scroll.setWidget(self.items_container)
        parent_layout.addWidget(items_scroll, 1)

    def _build_actions_section(self, parent_layout):
        """Construit la section des boutons d'action (Annuler commande / Valider / Prioritaire)."""
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.button_cancel = QPushButton()
        self.button_cancel.setIcon(_make_cancel_icon(22))
        self.button_cancel.setIconSize(QSize(22, 22))
        self.button_cancel.setObjectName("cancelButton")
        self.button_cancel.setEnabled(False)
        self.button_cancel.setFixedSize(32, 32)
        self.button_cancel.setToolTip("Annuler la commande")

        self.button_validate = QPushButton("Valider")
        self.button_validate.setObjectName("actionButton")
        self.button_validate.setEnabled(False)
        self.button_validate.setFixedHeight(32)

        self.button_priority = QPushButton("!")
        self.button_priority.setObjectName("priorityButton")
        self.button_priority.setCheckable(True)
        self.button_priority.setEnabled(False)
        self.button_priority.setFixedSize(32, 32)
        self.button_priority.setToolTip("Commande prioritaire")

        self.button_cancel.clicked.connect(self._handle_cancel_command)
        self.button_validate.clicked.connect(self._handle_validate_command)
        self.button_priority.clicked.connect(self._handle_toggle_priority)

        actions_layout.addWidget(self.button_cancel)
        actions_layout.addWidget(self.button_validate, 1)
        actions_layout.addWidget(self.button_priority)

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
            QPushButton#cancelButton {
                background-color: #d9534f;
                border: 1px solid #ac2925;
                border-radius: 7px;
                padding: 0px;
            }
            QPushButton#cancelButton:hover {
                background-color: #c9302c;
            }
            QPushButton#cancelButton:disabled {
                background-color: #2f3136;
                border-color: #3a3d43;
            }
            QPushButton#actionButton {
                background-color: #4f545e;
                border: 1px solid #7d8390;
                border-radius: 7px;
                color: #f5f5f5;
                font-size: 14px;
                font-weight: 700;
                padding: 4px 12px;
            }
            QPushButton#actionButton:hover {
                background-color: #626978;
            }
            QPushButton#actionButton:disabled {
                color: #8f949c;
                background-color: #3a3d43;
                border-color: #595d64;
            }
            QPushButton#priorityButton {
                background-color: #3a3d43;
                border: 1px solid #595d64;
                border-radius: 7px;
                color: #595d64;
                font-size: 16px;
                font-weight: 900;
            }
            QPushButton#priorityButton:hover:!checked {
                background-color: #4f545e;
                border-color: #7d8390;
                color: #c97a30;
            }
            QPushButton#priorityButton:checked {
                background-color: #5a1a1a;
                border: 2px solid #e74c3c;
                color: #e74c3c;
            }
            QPushButton#priorityButton:disabled {
                color: #3a3d43;
                background-color: #2f3136;
                border-color: #3a3d43;
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
        self.button_cancel.setEnabled(False)
        self.button_priority.setChecked(False)
        self.button_priority.setEnabled(False)
        self.button_validate.setEnabled(False)

    def _display_order_state(self, order: Dict):
        """Affiche l'état d'une commande active : titre, articles et boutons activés."""
        self.title_label.setText(f"Commande {order['id']}")
        self._refresh_items_display(order)
        self.button_cancel.setEnabled(True)
        self.button_priority.setEnabled(True)
        self.button_priority.setChecked(order.get("priority", False))
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

    def _handle_toggle_priority(self):
        """Bascule le statut prioritaire de la commande en cours et enregistre dans le JSON."""
        order_path = self._get_current_order_path()
        if not order_path:
            return
        try:
            set_prioritaire(str(order_path), self.button_priority.isChecked())
            self.command_changed.emit()
        except Exception as e:
            self.status_label.setText(f"Erreur priorité: {str(e)}")

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
        """Recharge les catégories depuis le JSON et crée les boutons, puis les arrange."""
        # Supprime les anciens boutons
        while self.menu_grid.count():
            item = self.menu_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._menu_button_widgets = []
        self._current_menu_columns = 0  # Force le ré-arrangement

        categories = get_menu_categories()
        visible_categories = [cat for cat in categories if not cat.get("hidden", False)]

        if not visible_categories:
            placeholder = QLabel("Aucune categorie trouvee.")
            placeholder.setStyleSheet("color: #d6d6d6; font-size: 14px;")
            self.menu_grid.addWidget(placeholder, 0, 0)
            self.menu_scroll.setFixedHeight(118)
            self.menu_container.adjustSize()
            return

        for category in visible_categories:
            label = category["name"]
            icon_path = category.get("icon_path")
            button = BoutonMenu(label, svg_path=icon_path, parent=self.menu_container)

            if not category.get("enabled", True):
                button.setEnabled(False)
                button.setToolTip("Categorie indisponible")
            elif not check_disponibilite_plat(label):
                button.setEnabled(False)
                button.setToolTip("Rupture de stock")
            else:
                button.clicked.connect(
                    lambda _checked=False, cat=category: self._on_category_button_clicked(cat["name"])
                )

            self._menu_button_widgets.append(button)

        self._arrange_menu_buttons()

    def _calculate_menu_columns(self) -> int:
        """Nombre de colonnes selon la largeur du viewport (boutons 120 px + 8 px d'écart)."""
        available = self.menu_scroll.viewport().width()
        if available <= 0:
            return 5
        return max(1, (available + 8) // (120 + 8))

    def _arrange_menu_buttons(self):
        """Replace les boutons dans la grille avec le nombre de colonnes adapté à la largeur."""
        if not self._menu_button_widgets:
            return

        columns = self._calculate_menu_columns()
        if columns == self._current_menu_columns and self.menu_grid.count() > 0:
            return  # Rien à faire si le nombre de colonnes n'a pas changé
        self._current_menu_columns = columns

        # Retire les boutons de la grille sans les supprimer
        while self.menu_grid.count():
            self.menu_grid.takeAt(0)

        # Remet les boutons dans la grille avec le nouveau nombre de colonnes
        for index, button in enumerate(self._menu_button_widgets):
            row = index // columns
            column = index % columns
            self.menu_grid.addWidget(button, row, column)
            button.show()

        # Met à jour la hauteur de la zone de défilement
        row_count = ((len(self._menu_button_widgets) - 1) // columns) + 1
        scroll_height = max(118, 24 + (row_count * 128))
        self.menu_scroll.setFixedHeight(scroll_height)

        # Recalcule la taille du conteneur pour que le centrage fonctionne
        self.menu_container.adjustSize()

    def eventFilter(self, source, event):
        """Réorganise les boutons du menu quand le viewport change de largeur."""
        if source is self.menu_scroll.viewport() and event.type() == QEvent.Type.Resize:
            self._arrange_menu_buttons()
        return super().eventFilter(source, event)

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
        """Appelé toutes les 2 secondes : met à jour la liste des articles si une commande est active."""
        order = self._get_current_order()
        if order:
            self._refresh_items_display(order)
        else:
            self._display_no_order_state()
