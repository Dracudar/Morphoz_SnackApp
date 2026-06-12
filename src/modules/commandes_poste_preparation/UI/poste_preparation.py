#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poste_preparation.py - Module du poste de préparation

Description:
    Affichage plein écran des plats en cours de préparation, filtrable par type
    (Pizza, Grillade, Frites, Salade composée, Crêpe). Les plats sont affichés
    en grille (3 colonnes) adaptée aux écrans tactiles 10".

Author :
    Dracudar

Version:
    2.0

Date de création :
    2026.06.08

Date de modification:
    2026.06.12
"""

from PySide6.QtCore import Qt, QTimer
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

from src.backend.data_sources import get_live_orders_prep
from src.modules.commandes_poste_preparation.UI.widgets.carte_plat import CartePlatWidget

_ALL_TYPES = ["Pizza", "Grillade", "Frites", "Salade composée", "Crêpe"]
_COLUMNS   = 3  # colonnes en grille (adapté à l'écran 10")

# ── Palette ───────────────────────────────────────────────────────────────────
_BG           = "#2f3136"
_TEXT_TITRE   = "#f5f5f5"
_BTN_INACTIF  = ("background-color: #3a3d43; color: #d6d6d6; border: 1px solid #60646c; "
                 "border-radius: 4px; padding: 5px 14px;")
_BTN_INACTIF_HOVER = "background-color: #4a4e55;"
_BTN_ACTIF    = ("background-color: #4a7fcb; color: #ffffff; border: 1px solid #4a7fcb; "
                 "border-radius: 4px; padding: 5px 14px; font-weight: 700;")
_BTN_ACTIF_HOVER = "background-color: #5a8fdb;"


class PostePreparationModule(QFrame):
    """Page plein écran du poste de préparation (grille 3 colonnes)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("postePreparation")
        self._active_filters: set[str] = set()
        self._filter_buttons: dict[str, QPushButton] = {}
        self._build_ui()
        self._build_timer()
        self.refresh()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        main_layout.addLayout(self._build_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: {_BG}; }}"
        )

        # Contenu scrollable : grille + stretch pour coller en haut
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(10)
        for col in range(_COLUMNS):
            self._grid_layout.setColumnStretch(col, 1)

        content_layout.addWidget(self._grid_container)
        content_layout.addStretch(1)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.setStyleSheet(f"QFrame#postePreparation {{ background-color: {_BG}; }}")

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(8)

        self._title_label = QLabel("Poste de préparation")
        self._title_label.setStyleSheet(
            f"color: {_TEXT_TITRE}; font-size: 19px; font-weight: 700;"
        )
        header.addWidget(self._title_label, 1)

        for plat_type in _ALL_TYPES:
            btn = QPushButton(plat_type)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.toggled.connect(lambda checked, t=plat_type: self._on_filter_toggled(t, checked))
            self._apply_btn_style(btn, active=False)
            header.addWidget(btn)
            self._filter_buttons[plat_type] = btn

        return header

    def _build_timer(self):
        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    # ── Filtres ───────────────────────────────────────────────────────────────

    def _on_filter_toggled(self, plat_type: str, checked: bool):
        if checked:
            self._active_filters.add(plat_type)
        else:
            self._active_filters.discard(plat_type)
        self._apply_btn_style(self._filter_buttons[plat_type], active=checked)
        self.refresh()

    def _apply_btn_style(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(
                f"QPushButton {{ {_BTN_ACTIF} }}"
                f"QPushButton:hover {{ {_BTN_ACTIF_HOVER} }}"
            )
        else:
            btn.setStyleSheet(
                f"QPushButton {{ {_BTN_INACTIF} }}"
                f"QPushButton:hover {{ {_BTN_INACTIF_HOVER} }}"
            )

    # ── Données ───────────────────────────────────────────────────────────────

    def _clear_grid(self):
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def refresh(self):
        """Recharge les plats depuis le disque et reconstruit la grille."""
        plats = get_live_orders_prep()
        if self._active_filters:
            plats = [p for p in plats if p["plat"] in self._active_filters]

        self._clear_grid()

        count = len(plats)
        plat_word = "plat" if count <= 1 else "plats"
        self._title_label.setText(
            f"Poste de préparation  —  {count} {plat_word} en cours"
        )

        for i, plat in enumerate(plats):
            row, col = divmod(i, _COLUMNS)
            card = CartePlatWidget(plat, self._on_state_changed)
            self._grid_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)

    def _on_state_changed(self, _context=None):
        """Rappelé par le backend après un changement de statut."""
        self.refresh()
