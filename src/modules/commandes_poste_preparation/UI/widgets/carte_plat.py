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
    2.4

Date de création :
    2026.06.08

Date de modification:
    2026.06.13
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

from src.modules.commandes_suivi.backend.commandes_suivi_gestion import livrer_plat, plat_prêt, retour_preparation
from src.utils.tactile import BoutonTactile, ScrollAreaTactile

# ── Dimensions ────────────────────────────────────────────────────────────────
CARD_H = 250   # hauteur fixe pour uniformité de la grille

# ── Palette ───────────────────────────────────────────────────────────────────
_BG_CARD      = "#3a3d43"
_BORDER       = "#60646c"
_TEXT_ID      = "#f5f5f5"   # ID : le plus visible (numéro souligné)
_TEXT_NOM     = "#a8acb3"   # Nom : intermédiaire
_TEXT_COMP    = "#f0f0f0"   # Composition : blanc cassé
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

_BTN_RETOUR_COLOR = "#5c6370"
_BTN_RETOUR_LABEL = "↩  Prépa"

_COMP_FONT = "font-size: 13px;"


class CartePlatWidget(QFrame):
    """Carte tactile à hauteur fixe — hiérarchie ID > composition > nom."""

    def __init__(self, plat: dict, on_action: Callable[[], None], scroll_area: ScrollAreaTactile, parent=None):
        super().__init__(parent)
        self._plat = plat
        self._on_action = on_action
        self._scroll_area = scroll_area
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

        id_val = self._plat["id"]
        parts  = id_val.split("-", 1)
        if len(parts) == 2:
            id_html = (
                f'{parts[0]}-'
                f'<span style="text-decoration: underline;">{parts[1]}</span>'
            )
        else:
            id_html = id_val

        id_label = QLabel(id_html)
        id_label.setTextFormat(Qt.TextFormat.RichText)
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

        # ── Nom du plat ───────────────────────────────────────────────────────
        nom_label = QLabel(self._plat["nom"])
        nom_label.setWordWrap(True)
        nom_label.setStyleSheet(
            f"color: {_TEXT_NOM}; font-size: 13px;"
        )
        layout.addWidget(nom_label)

        # ── Composition ───────────────────────────────────────────────────────
        self._add_composition(layout)

        layout.addStretch(1)

        # ── Bouton(s) d'action ────────────────────────────────────────────────
        btn_label = _BTN_LABEL.get(status_lower)
        btn_color = _BTN_COLOR.get(status_lower)

        if btn_label and btn_color:
            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)

            btn = BoutonTactile(btn_label, self._scroll_area)
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
            btn_row.addWidget(btn)

            if status_lower == "prêt":
                btn_retour = BoutonTactile(_BTN_RETOUR_LABEL, self._scroll_area)
                btn_retour.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_retour.setMinimumHeight(44)
                btn_retour.setFixedWidth(90)
                btn_retour.setStyleSheet(
                    f"QPushButton {{ background-color: {_BTN_RETOUR_COLOR}; color: #d0d3d8; border: none; "
                    f"border-radius: 6px; padding: 8px; font-weight: 600; font-size: 13px; }}"
                    f"QPushButton:hover {{ background-color: {_BTN_RETOUR_COLOR}cc; }}"
                    f"QPushButton:pressed {{ background-color: {_BTN_RETOUR_COLOR}99; }}"
                )
                btn_retour.clicked.connect(self._action_retour_preparation)
                btn_row.addWidget(btn_retour)

            layout.addLayout(btn_row)

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
        standard    = [i for i in ingredients if i not in ajouts]

        sub = QVBoxLayout()
        sub.setSpacing(2)
        sub.setContentsMargins(0, 0, 0, 0)

        if base:
            sub.addWidget(self._comp_label(f"Base : {base}", _TEXT_COMP))

        for item in standard:
            sub.addLayout(self._comp_row("•", item, _TEXT_COMP))

        for item in sorted(retraits):
            sub.addLayout(self._comp_row("−", item, _RETRAIT_CLR, bold=True))

        for item in sorted(ajouts):
            sub.addLayout(self._comp_row("+", item, _AJOUT_CLR, bold=True))

        layout.addLayout(sub)

    def _add_salade_composition(self, layout: QVBoxLayout, comp: dict):
        ingredients = comp.get("Ingrédients", [])
        if not ingredients:
            return
        sub = QVBoxLayout()
        sub.setSpacing(2)
        sub.setContentsMargins(0, 0, 0, 0)
        for item in ingredients:
            sub.addLayout(self._comp_row("•", item, _TEXT_COMP))
        layout.addLayout(sub)

    def _comp_label(self, text: str, color: str, bold: bool = False) -> QLabel:
        """Label pleine largeur (sans marqueur) pour Base et lignes sans puce."""
        lbl = QLabel(text)
        weight = "font-weight: 700;" if bold else ""
        lbl.setStyleSheet(f"color: {color}; {_COMP_FONT} {weight}")
        return lbl

    def _comp_row(self, marker: str, text: str, color: str, bold: bool = False) -> QHBoxLayout:
        """Ligne avec marqueur à largeur fixe pour un alignement parfait du texte."""
        row = QHBoxLayout()
        row.setSpacing(4)
        row.setContentsMargins(0, 0, 0, 0)

        weight = "font-weight: 700;" if bold else ""
        style  = f"color: {color}; {_COMP_FONT} {weight}"

        m_lbl = QLabel(marker)
        m_lbl.setFixedWidth(14)      # largeur fixe : tous les textes s'alignent
        m_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        m_lbl.setStyleSheet(style)
        row.addWidget(m_lbl)

        t_lbl = QLabel(text)
        t_lbl.setWordWrap(True)
        t_lbl.setStyleSheet(style)
        row.addWidget(t_lbl, 1)

        return row

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

    def _action_retour_preparation(self):
        retour_preparation(
            None,
            str(self._plat["file"]),
            self._plat["id"],
            lambda _: self._on_action(),
        )
