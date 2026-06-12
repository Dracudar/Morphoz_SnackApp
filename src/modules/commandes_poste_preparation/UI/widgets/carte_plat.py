#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
carte_plat.py - Widget carte d'un plat pour le poste de préparation

Description:
    Affiche un plat (ID, nom, composition, bouton contextuel) sous forme de
    carte compacte conçue pour écran tactile 10".
    Structure (haut → bas) : ID · Nom · Composition · Bouton unique.

Author :
    Dracudar

Version:
    2.0

Date de création :
    2026.06.08

Date de modification:
    2026.06.12
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from src.modules.commandes_suivi.backend.commandes_suivi_gestion import livrer_plat, plat_prêt

# ── Palette ───────────────────────────────────────────────────────────────────
_BG_CARD     = "#3a3d43"
_BORDER      = "#60646c"
_TEXT_ID     = "#6b7280"
_TEXT_NOM    = "#f5f5f5"
_TEXT_COMP   = "#a8acb3"
_AJOUT_CLR   = "#4caf50"
_RETRAIT_CLR = "#e05c5c"

_STATUS_BORDER = {
    "en préparation": "#c97a30",
    "prêt":           "#d4a017",
}

_BTN_COLOR = {
    "en préparation": "#d4a017",
    "prêt":           "#4caf50",
}

_BTN_LABEL = {
    "en préparation": "✓  Marquer Prêt",
    "prêt":           "⬆  Livré",
}


class CartePlatWidget(QFrame):
    """Carte tactile affichant un plat avec composition et bouton d'action unique."""

    def __init__(self, plat: dict, on_action: Callable[[], None], parent=None):
        super().__init__(parent)
        self._plat = plat
        self._on_action = on_action
        self.setObjectName("cartePlat")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._build_ui()

    def _build_ui(self):
        status_lower = self._plat["status"].lower()
        accent = _STATUS_BORDER.get(status_lower, _BORDER)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        # ── ID ────────────────────────────────────────────────────────────────
        id_label = QLabel(self._plat["id"])
        id_label.setStyleSheet(
            f"color: {_TEXT_ID}; font-size: 11px; font-family: monospace;"
        )
        layout.addWidget(id_label)

        # ── Nom du plat ───────────────────────────────────────────────────────
        nom_label = QLabel(self._plat["nom"])
        nom_label.setWordWrap(True)
        nom_label.setStyleSheet(
            f"color: {_TEXT_NOM}; font-size: 15px; font-weight: 700;"
        )
        layout.addWidget(nom_label)

        # ── Composition ───────────────────────────────────────────────────────
        self._add_composition(layout)

        layout.addStretch(1)

        # ── Bouton contextuel unique ──────────────────────────────────────────
        btn_label = _BTN_LABEL.get(status_lower)
        btn_color = _BTN_COLOR.get(status_lower)

        if btn_label and btn_color:
            btn = QPushButton(btn_label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(44)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {btn_color}; color: #1a1a1a; border: none; "
                f"border-radius: 6px; padding: 8px; font-weight: 700; font-size: 14px; }}"
                f"QPushButton:hover {{ background-color: {btn_color}cc; }}"
                f"QPushButton:pressed {{ background-color: {btn_color}99; }}"
            )
            if status_lower == "en préparation":
                btn.clicked.connect(self._action_prêt)
            else:
                btn.clicked.connect(self._action_livré)
            layout.addWidget(btn)

        self.setStyleSheet(
            f"""
            QFrame#cartePlat {{
                background-color: {_BG_CARD};
                border: 1px solid {_BORDER};
                border-left: 4px solid {accent};
                border-radius: 8px;
            }}
            """
        )

    # ── Composition ───────────────────────────────────────────────────────────

    def _add_composition(self, layout: QVBoxLayout):
        comp = self._plat.get("composition", {})
        plat_type = self._plat.get("plat", "")

        if not comp:
            return

        if plat_type == "Pizza":
            self._add_pizza_composition(layout, comp)
        else:
            text = self._format_other(plat_type, comp)
            if text:
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(f"color: {_TEXT_COMP}; font-size: 12px;")
                layout.addWidget(lbl)

    def _add_pizza_composition(self, layout: QVBoxLayout, comp: dict):
        base = comp.get("Base", "")
        ingredients = comp.get("Ingrédients", [])
        ajouts = set(comp.get("Ajouts", []))
        retraits = set(comp.get("Retraits", []))

        if base:
            lbl = QLabel(f"Base : {base}")
            lbl.setStyleSheet(f"color: {_TEXT_COMP}; font-size: 12px;")
            layout.addWidget(lbl)

        # Ingrédients standards (ni ajout déclaré, ni retrait)
        standard = [i for i in ingredients if i not in ajouts]
        if standard:
            lbl = QLabel(", ".join(standard))
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {_TEXT_COMP}; font-size: 12px;")
            layout.addWidget(lbl)

        # Ajouts (vert)
        for item in sorted(ajouts):
            lbl = QLabel(f"+ {item}")
            lbl.setStyleSheet(
                f"color: {_AJOUT_CLR}; font-size: 12px; font-weight: 700;"
            )
            layout.addWidget(lbl)

        # Retraits (rouge barré)
        for item in sorted(retraits):
            lbl = QLabel(f"− {item}")
            font = lbl.font()
            font.setStrikeOut(True)
            lbl.setFont(font)
            lbl.setStyleSheet(
                f"color: {_RETRAIT_CLR}; font-size: 12px; font-weight: 700;"
            )
            layout.addWidget(lbl)

    def _format_other(self, plat_type: str, comp: dict) -> str:
        if plat_type == "Grillade":
            viandes = comp.get("Viandes", {})
            accompagnement = comp.get("Accompagnement", "")
            parts = []
            if isinstance(viandes, dict) and viandes:
                viandes_str = ", ".join(
                    f"{v} ×{q}" if int(q) > 1 else v for v, q in viandes.items()
                )
                parts.append(f"Viandes : {viandes_str}")
            if accompagnement:
                parts.append(f"Accompagnement : {accompagnement}")
            return "\n".join(parts)

        if plat_type == "Crêpe":
            garniture = comp.get("Garniture", [])
            if garniture:
                return "Garniture : " + ", ".join(garniture)

        return ""

    # ── Actions ───────────────────────────────────────────────────────────────

    def _action_prêt(self):
        plat_prêt(
            None,
            str(self._plat["file"]),
            self._plat["id"],
            lambda _: self._on_action(),
        )

    def _action_livré(self):
        livrer_plat(
            None,
            str(self._plat["file"]),
            self._plat["id"],
            lambda _: self._on_action(),
        )
