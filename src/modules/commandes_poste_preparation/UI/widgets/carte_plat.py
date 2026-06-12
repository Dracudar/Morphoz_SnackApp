#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
carte_plat.py - Widget carte d'un plat pour le poste de préparation

Description:
    Affiche un plat sous forme de carte à hauteur fixe pour écran tactile 10".
    Hiérarchie visuelle (haut → bas) : ID · Composition · Nom · Bouton unique.
    Commandes prioritaires : cadre rouge complet + badge inline sur la ligne ID.

Author :
    Dracudar

Version:
    2.2

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
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from src.modules.commandes_suivi.backend.commandes_suivi_gestion import livrer_plat, plat_prêt

# ── Dimensions ────────────────────────────────────────────────────────────────
CARD_H = 250   # hauteur fixe pour uniformité de la grille

# ── Palette ───────────────────────────────────────────────────────────────────
_BG_CARD      = "#3a3d43"
_BORDER       = "#60646c"
_TEXT_ID      = "#f5f5f5"   # ID : le plus visible
_TEXT_NOM     = "#7a7f87"   # Nom : discret (information secondaire)
_TEXT_COMP    = "#a8acb3"   # Composition
_AJOUT_CLR    = "#4caf50"
_RETRAIT_CLR  = "#e05c5c"
_PRIORITY_CLR = "#e53e3e"

_BTN_COLOR = {
    "en préparation": "#d4a017",
    "prêt":           "#4caf50",
}

_BTN_LABEL = {
    "en préparation": "✓  Marquer Prêt",
    "prêt":           "⬆  Livré",
}

_COMP_FONT = "font-size: 13px;"


class CartePlatWidget(QFrame):
    """Carte tactile à hauteur fixe — hiérarchie ID > composition > nom."""

    def __init__(self, plat: dict, on_action: Callable[[], None], parent=None):
        super().__init__(parent)
        self._plat = plat
        self._on_action = on_action
        self.setObjectName("cartePlat")
        self.setFixedHeight(CARD_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._build_ui()

    def _build_ui(self):
        status_lower = self._plat["status"].lower()
        prioritaire  = self._plat.get("prioritaire", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # ── Ligne ID + badge prioritaire ─────────────────────────────────────
        id_row = QHBoxLayout()
        id_row.setSpacing(6)

        id_label = QLabel(self._plat["id"])
        id_label.setStyleSheet(
            f"color: {_TEXT_ID}; font-size: 15px; font-weight: 700; font-family: monospace;"
        )
        id_row.addWidget(id_label, 1)

        if prioritaire:
            badge = QLabel("⚡ PRIORITAIRE")
            badge.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            badge.setStyleSheet(
                f"color: {_PRIORITY_CLR}; font-size: 11px; font-weight: 700;"
            )
            id_row.addWidget(badge)

        layout.addLayout(id_row)

        # ── Composition (avant le nom) ────────────────────────────────────────
        self._add_composition(layout)

        # ── Nom du plat (discret, information secondaire) ─────────────────────
        nom_label = QLabel(self._plat["nom"])
        nom_label.setWordWrap(True)
        nom_label.setStyleSheet(
            f"color: {_TEXT_NOM}; font-size: 12px;"
        )
        layout.addWidget(nom_label)

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

        # Cadre : rouge complet si prioritaire, sinon bordure neutre
        if prioritaire:
            border_style = f"border: 2px solid {_PRIORITY_CLR};"
        else:
            border_style = f"border: 1px solid {_BORDER};"

        self.setStyleSheet(
            f"""
            QFrame#cartePlat {{
                background-color: {_BG_CARD};
                {border_style}
                border-radius: 8px;
            }}
            """
        )

    # ── Composition ───────────────────────────────────────────────────────────

    def _add_composition(self, layout: QVBoxLayout):
        comp      = self._plat.get("composition", {})
        plat_type = self._plat.get("plat", "")

        if not comp:
            return

        if plat_type == "Pizza":
            self._add_pizza_composition(layout, comp)
        elif plat_type == "Salade composée":
            self._add_salade_composition(layout, comp)
        else:
            text = self._format_other(plat_type, comp)
            if text:
                lbl = QLabel(text)
                lbl.setWordWrap(True)
                lbl.setStyleSheet(f"color: {_TEXT_COMP}; {_COMP_FONT}")
                layout.addWidget(lbl)

    def _add_pizza_composition(self, layout: QVBoxLayout, comp: dict):
        base        = comp.get("Base", "")
        ingredients = comp.get("Ingrédients", [])
        ajouts      = set(comp.get("Ajouts", []))
        retraits    = set(comp.get("Retraits", []))

        if base:
            lbl = QLabel(f"Base : {base}")
            lbl.setStyleSheet(f"color: {_TEXT_COMP}; {_COMP_FONT}")
            layout.addWidget(lbl)

        standard = [i for i in ingredients if i not in ajouts]
        if standard:
            lbl = QLabel("\n".join(f"• {i}" for i in standard))
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {_TEXT_COMP}; {_COMP_FONT}")
            layout.addWidget(lbl)

        for item in sorted(ajouts):
            lbl = QLabel(f"+ {item}")
            lbl.setStyleSheet(f"color: {_AJOUT_CLR}; {_COMP_FONT} font-weight: 700;")
            layout.addWidget(lbl)

        for item in sorted(retraits):
            lbl = QLabel(f"− {item}")
            font = lbl.font()
            font.setStrikeOut(True)
            lbl.setFont(font)
            lbl.setStyleSheet(f"color: {_RETRAIT_CLR}; {_COMP_FONT} font-weight: 700;")
            layout.addWidget(lbl)

    def _add_salade_composition(self, layout: QVBoxLayout, comp: dict):
        ingredients = comp.get("Ingrédients", [])
        if ingredients:
            lbl = QLabel("\n".join(f"• {i}" for i in ingredients))
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {_TEXT_COMP}; {_COMP_FONT}")
            layout.addWidget(lbl)

    def _format_other(self, plat_type: str, comp: dict) -> str:
        if plat_type == "Grillade":
            viandes        = comp.get("Viandes", {})
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
