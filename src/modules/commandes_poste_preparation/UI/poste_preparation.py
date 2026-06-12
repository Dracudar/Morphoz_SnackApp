#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poste_preparation.py - Module du poste de préparation

Description:
    Affichage plein écran des plats en cours de préparation, filtrable par type
    (Pizza, Grillade, Frites, Salade composée, Crêpe). Chaque plat est représenté
    par une carte avec ses détails et ses boutons d'action (Prêt / Livré).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.08

Date de modification:
    2026.06.08
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.utils.tactile import ScrollAreaTactile
from src.backend.data_sources import get_live_orders_prep
from src.modules.commandes_poste_preparation.UI.widgets.carte_plat import CartePlatWidget

_ALL_TYPES = ["Pizza", "Grillade", "Frites", "Salade composée", "Crêpe"]

# ── Palette ──────────────────────────────────────────────────────────────────
_BG           = "#2f3136"
_TEXT_TITRE   = "#f5f5f5"
_BTN_INACTIF  = ("background-color: #3a3d43; color: #d6d6d6; border: 1px solid #60646c; "
                 "border-radius: 4px; padding: 5px 14px;")
_BTN_INACTIF_HOVER = "background-color: #4a4e55;"
_BTN_ACTIF    = ("background-color: #4a7fcb; color: #ffffff; border: 1px solid #4a7fcb; "
                 "border-radius: 4px; padding: 5px 14px; font-weight: 700;")
_BTN_ACTIF_HOVER = "background-color: #5a8fdb;"


class PostePreparationModule(QFrame):
    """Page plein écran du poste de préparation."""

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

        scroll = ScrollAreaTactile(_BG)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(10)
        self._list_layout.addStretch()
        scroll.setWidget(self._list_container)

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

    def _clear_list(self):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh(self):
        """Recharge les plats depuis le disque et reconstruit la liste."""
        plats = get_live_orders_prep()
        if self._active_filters:
            plats = [p for p in plats if p["plat"] in self._active_filters]

        self._clear_list()

        count = len(plats)
        plat_word = "plat" if count <= 1 else "plats"
        self._title_label.setText(
            f"Poste de préparation  —  {count} {plat_word} en cours"
        )

        for plat in plats:
            card = CartePlatWidget(plat, self._on_state_changed)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)

    def _on_state_changed(self, _context=None):
        """Rappelé par le backend après un changement de statut."""
        self.refresh()
