#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
carte_plat.py - Widget carte d'un plat pour le poste de préparation

Description:
    Affiche les détails complets d'un plat en cours (ID, nom, composition)
    avec les boutons d'action pour changer son statut (Prêt / Livré).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.08

Date de modification:
    2026.06.08
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.modules.commandes_suivi.backend.commandes_suivi_gestion import livrer_plat, plat_prêt

# ── Palette ──────────────────────────────────────────────────────────────────
_BG_CARD    = "#3a3d43"
_BORDER     = "#60646c"
_TEXT_ID    = "#f5f5f5"
_TEXT_NOM   = "#d6d6d6"
_TEXT_COMP  = "#a8acb3"

_STATUTS = {
    "en préparation": ("#7a4a1a", "#c97a30", "En préparation"),
    "prêt":           ("#5e4a00", "#d4a017", "Prêt"),
}


class CartePlatWidget(QFrame):
    """Carte affichant un plat avec sa composition et ses boutons d'action."""

    def __init__(self, plat: dict, on_action: Callable[[], None], parent=None):
        super().__init__(parent)
        self._plat = plat
        self._on_action = on_action
        self.setObjectName("cartePlat")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # ── ID + badge statut ──────────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        id_label = QLabel(self._plat["id"])
        id_label.setStyleSheet(
            f"color: {_TEXT_ID}; font-size: 15px; font-weight: 700; font-family: monospace;"
        )
        header_row.addWidget(id_label, 1)
        header_row.addWidget(self._build_badge(self._plat["status"]))
        layout.addLayout(header_row)

        # ── Nom du plat ────────────────────────────────────────────────────────
        nom_label = QLabel(self._plat["nom"])
        nom_label.setStyleSheet(f"color: {_TEXT_NOM}; font-size: 14px; font-weight: 600;")
        layout.addWidget(nom_label)

        # ── Composition ────────────────────────────────────────────────────────
        comp_text = self._format_composition()
        if comp_text:
            comp_label = QLabel(comp_text)
            comp_label.setWordWrap(True)
            comp_label.setStyleSheet(f"color: {_TEXT_COMP}; font-size: 13px;")
            layout.addWidget(comp_label)

        # ── Boutons d'action ───────────────────────────────────────────────────
        status_lower = self._plat["status"].lower()
        can_prêt  = status_lower == "en préparation"
        can_livré = status_lower == "prêt"

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_prêt = QPushButton("✓  Prêt")
        btn_prêt.setEnabled(can_prêt)
        btn_prêt.setCursor(
            Qt.CursorShape.PointingHandCursor if can_prêt else Qt.CursorShape.ArrowCursor
        )
        btn_prêt.clicked.connect(self._action_prêt)
        self._style_btn(btn_prêt, "#d4a017", can_prêt)
        btn_row.addWidget(btn_prêt)

        btn_livré = QPushButton("⬆  Livré")
        btn_livré.setEnabled(can_livré)
        btn_livré.setCursor(
            Qt.CursorShape.PointingHandCursor if can_livré else Qt.CursorShape.ArrowCursor
        )
        btn_livré.clicked.connect(self._action_livré)
        self._style_btn(btn_livré, "#4caf50", can_livré)
        btn_row.addWidget(btn_livré)

        layout.addLayout(btn_row)

        self.setStyleSheet(
            f"""
            QFrame#cartePlat {{
                background-color: {_BG_CARD};
                border: 1px solid {_BORDER};
                border-radius: 8px;
            }}
            """
        )

    # ── Helpers UI ─────────────────────────────────────────────────────────────

    def _build_badge(self, status: str) -> QLabel:
        key = status.lower()
        bg, fg, text = _STATUTS.get(key, ("#3a3d43", "#7a7f87", status or "?"))
        badge = QLabel(text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 1px solid {fg}; "
            f"border-radius: 4px; font-size: 12px; font-weight: 600; padding: 2px 8px;"
        )
        return badge

    def _style_btn(self, btn: QPushButton, color: str, enabled: bool):
        if enabled:
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {color}; color: #1a1a1a; border: none; "
                f"border-radius: 4px; padding: 6px 20px; font-weight: 700; font-size: 13px; }}"
                f"QPushButton:hover {{ background-color: {color}cc; }}"
                f"QPushButton:pressed {{ background-color: {color}99; }}"
            )
        else:
            btn.setStyleSheet(
                "QPushButton { background-color: #2a2d32; color: #555; border: 1px solid #3a3d43; "
                "border-radius: 4px; padding: 6px 20px; font-size: 13px; }"
            )

    def _format_composition(self) -> str:
        """Formate la composition du plat selon son type."""
        comp = self._plat.get("composition", {})
        plat_type = self._plat.get("plat", "")

        if not comp:
            return ""

        if plat_type == "Pizza":
            base = comp.get("Base", "")
            ingredients = comp.get("Ingrédients", [])
            parts = []
            if base:
                parts.append(f"Base : {base}")
            if ingredients:
                parts.append("Ingrédients : " + ", ".join(ingredients))
            return "\n".join(parts)

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

    # ── Actions ────────────────────────────────────────────────────────────────

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
