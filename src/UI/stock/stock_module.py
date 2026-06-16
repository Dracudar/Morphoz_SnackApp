#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stock_module.py

Description:
    Interface Qt/PySide6 de consultation et gestion du stock.
    Panneau gauche (50 %) : sections pliables par famille, barre de recherche libre.
    Chaque ligne d'article affiche son nom et trois tags fixes alignés à droite :
      - Carte  (coloré si référencé dans la carte active, grisé sinon)
      - Suivi  (coloré si suivi unitaire actif, grisé sinon)
      - État   (En stock / Rupture)
    Panneau droit (50 %) : détail de l'article sélectionné avec formulaire
    d'édition (catégorie, nom, suivi quantité ON/OFF, valeurs de stock,
    statut OutOfStock) et bouton d'enregistrement.

    La construction de la liste (vue_liste.py) et du formulaire de détail
    (formulaire_edition.py) sont mélangées (mixins) dans StockModule, qui
    assure l'assemblage de l'interface et le rafraîchissement périodique.

Author :
    Dracudar

Version:
    2.4

Date de création :
    2025.05.29

Date de modification:
    2026.06.16
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.utils.tactile import ScrollAreaTactile
from src.backend.data.stock import get_stock_cache, get_stock_data
from src.UI.stock.formulaire_edition import _FormulaireEditionMixin
from src.UI.stock.utilitaires import (
    _BG_MAIN,
    _BG_RIGHT,
    _BG_SECTION,
    _BORDER_ITEM,
    _BORDER_MAIN,
    _BORDER_SECTION,
    _build_carte_ingredients_set,
    _build_prep_data,
    _CLR_IN_STOCK,
    _TEXT_ITEM,
    _TEXT_TITLE,
)
from src.UI.stock.vue_liste import _VueListeMixin


# ── Module principal ──────────────────────────────────────────────────────────

class StockModule(QFrame, _VueListeMixin, _FormulaireEditionMixin):
    """Module de consultation et gestion du stock."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("stockModule")
        self._sections_expanded: dict = {}
        self._selected_path: Optional[list] = None

        # Références vers les labels lecture seule du panneau de détail
        self._detail_fichier_lbl:    Optional[QLabel] = None
        self._detail_cache_lbl:      Optional[QLabel] = None
        self._detail_prep_lbl:       Optional[QLabel] = None
        self._detail_stock_reel_lbl: Optional[QLabel] = None

        self._build_ui()
        self._build_timer()
        self.refresh()

    # ── Construction de l'interface ─────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(8)

        title = QLabel("Gestion du stock")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("sectionTitle")
        main_layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Panneau gauche : recherche + liste ─────────────────────────────
        left_frame = QFrame()
        left_frame.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(6)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Rechercher un article…")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.textChanged.connect(self.refresh)
        search_row.addWidget(self.search_field, 1)
        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setToolTip("Ajouter un article")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            f"QPushButton {{ background-color: #1a4a2a; color: {_CLR_IN_STOCK};"
            f" border: 1px solid {_CLR_IN_STOCK}; border-radius: 4px;"
            f" font-size: 18px; font-weight: 700; }}"
            f" QPushButton:hover {{ background-color: #1e5e32; }}"
        )
        add_btn.clicked.connect(self._on_add_item_clicked)
        search_row.addWidget(add_btn)
        left_layout.addLayout(search_row)

        self.scroll_area = ScrollAreaTactile(_BG_MAIN)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.list_container)
        left_layout.addWidget(self.scroll_area, 1)

        splitter.addWidget(left_frame)

        # ── Panneau droit : détail / édition ───────────────────────────────
        right_frame = QFrame()
        right_frame.setObjectName("rightPanel")
        right_frame_lyt = QVBoxLayout(right_frame)
        right_frame_lyt.setContentsMargins(2, 2, 2, 2)
        right_frame_lyt.setSpacing(0)
        self.right_scroll = ScrollAreaTactile(_BG_RIGHT)
        right_frame_lyt.addWidget(self.right_scroll)
        self._detail_widget: Optional[QWidget] = None
        self._show_empty_detail()
        splitter.addWidget(right_frame)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter, 1)

        self.setStyleSheet(
            f"""
            QFrame#stockModule {{
                background-color: {_BG_MAIN};
                border: 1px solid {_BORDER_MAIN};
            }}
            QFrame#leftPanel {{
                background-color: {_BG_MAIN};
                border: 1px solid {_BORDER_SECTION};
                border-radius: 6px;
            }}
            QFrame#rightPanel {{
                background-color: {_BG_RIGHT};
                border: 1px solid {_BORDER_SECTION};
                border-radius: 6px;
            }}
            QFrame#subgroupFrame {{
                background-color: {_BG_SECTION};
                border: 1px solid {_BORDER_ITEM};
                border-radius: 4px;
            }}
            QLabel#sectionTitle {{
                color: {_TEXT_TITLE};
                font-size: 22px;
                font-weight: 700;
                padding: 4px;
            }}
            QLineEdit {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 6px;
                padding: 6px 8px;
            }}
            QComboBox {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 28px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                selection-background-color: #4f545e;
            }}
            QSpinBox {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 28px;
            }}
            QCheckBox {{
                color: {_TEXT_ITEM};
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            """
        )

    def _build_timer(self) -> None:
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(10_000)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()

    # ── Rafraîchissement principal ──────────────────────────────────────────

    def refresh(self) -> None:
        file_data       = get_stock_data()
        cache_obj       = get_stock_cache()
        cache_data      = cache_obj.data if cache_obj is not None else {}
        carte_set       = _build_carte_ingredients_set()
        by_nom, by_plat = _build_prep_data()
        query           = self.search_field.text().strip().lower()

        self._clear_list()
        for section_name, section_node in file_data.items():
            if not isinstance(section_node, dict):
                continue
            section_widget = self._build_section(
                section_name, section_node, carte_set, query,
            )
            if section_widget is not None:
                self.list_layout.insertWidget(self.list_layout.count() - 1, section_widget)

        # Mettre à jour uniquement les labels lecture seule du détail
        self._update_detail_readonly(file_data, cache_data, by_nom, by_plat)

    def _clear_list(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
