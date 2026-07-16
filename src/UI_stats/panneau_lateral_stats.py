#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
panneau_lateral_stats.py - Volet latéral de la vue Historique/Statistiques allégée

Description:
    Volet de navigation pour la vue allégée Statistiques + Historique +
    Journal : bascule entre les trois pages, plein écran, quitter. S'affiche
    en superposition sur le contenu principal via un bouton hamburger dans la
    barre de navigation. Le dossier data se choisit désormais uniquement
    depuis le launcher (accessible via le choix de fermeture "Revenir au
    launcher") : pas de page Paramètres tant qu'aucun réglage spécifique à ce
    mode n'existe.

Author :
    Dracudar

Version:
    2.1

Date de création :
    2026.07.05

Date de modification:
    2026.07.16
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.UI.utils.icones import icone_coloree

# ── Palette ───────────────────────────────────────────────────────────────────
_BG          = "#1e2124"
_BG_HOVER    = "#2c2f33"
_BG_ACTIF    = "#4a7fcb"
_CLR_TEXTE   = "#e8e8e8"
_CLR_DANGER  = "#e05c5c"
_CLR_SEP     = "#36393f"
_HAUTEUR_ITEM = 50
_ICON_SIZE    = QSize(20, 20)

_STYLE_ITEM = f"""
    QPushButton {{
        background-color: {_BG};
        color: {_CLR_TEXTE};
        border: none;
        text-align: left;
        padding: 0 20px;
        font-size: 14px;
        min-height: {_HAUTEUR_ITEM}px;
    }}
    QPushButton:hover {{ background-color: {_BG_HOVER}; }}
    QPushButton:checked {{ background-color: {_BG_ACTIF}; font-weight: 700; }}
"""

_STYLE_DANGER = f"""
    QPushButton {{
        background-color: {_BG};
        color: {_CLR_DANGER};
        border: none;
        text-align: left;
        padding: 0 20px;
        font-size: 14px;
        min-height: {_HAUTEUR_ITEM}px;
    }}
    QPushButton:hover {{ background-color: #3a1e1e; }}
"""

_STYLE_FERMER = f"""
    QPushButton {{
        color: #999;
        background: transparent;
        border: none;
        font-size: 18px;
    }}
    QPushButton:hover {{ color: {_CLR_TEXTE}; background-color: {_BG_HOVER}; }}
"""

# (icône SVG, label affiché, identifiant de page)
_ITEMS_NAV = [
    ("stats.svg",      "Statistiques",   "stats"),
    ("historique.svg", "Historique",     "historique"),
    ("log.svg",        "Journal",        "logs"),
]


class VoletStats(QFrame):
    """Volet latéral de la vue Historique/Statistiques (superposition dynamique)."""

    page_demandee      = Signal(str)  # "stats" | "historique" | "logs"
    action_app_demande = Signal(str)  # "fullscreen" | "quit"
    fermeture_demandee  = Signal()    # croix cliquée → la fenêtre parente doit aussi masquer l'overlay

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self._btn_plein_ecran: QPushButton | None = None
        self._boutons_nav: dict[str, QPushButton] = {}
        self._build_ui()
        self.hide()

    # ── API publique ──────────────────────────────────────────────────────────

    def maj_etat_plein_ecran(self, actif: bool):
        """Met à jour le libellé et l'état coché du bouton plein écran."""
        if self._btn_plein_ecran:
            self._btn_plein_ecran.setChecked(actif)
            self._btn_plein_ecran.setText(
                "  Quitter plein écran" if actif else "  Plein écran"
            )

    def maj_page_active(self, page_id: str):
        """Met en évidence le bouton de la page actuellement affichée."""
        for identifiant, bouton in self._boutons_nav.items():
            bouton.setChecked(identifiant == page_id)

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"QFrame {{ background-color: {_BG}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())

        for icone, label, page_id in _ITEMS_NAV:
            btn = self._bouton_item(f"  {label}", checkable=True, icone=icone)
            btn.clicked.connect(lambda _, p=page_id: self._naviguer(p))
            self._boutons_nav[page_id] = btn
            layout.addWidget(btn)

        layout.addWidget(self._separateur())
        layout.addStretch(1)
        layout.addWidget(self._separateur())

        self._btn_plein_ecran = self._bouton_item(
            "  Plein écran", checkable=True, icone="screen.svg"
        )
        self._btn_plein_ecran.clicked.connect(
            lambda: self.action_app_demande.emit("fullscreen")
        )
        layout.addWidget(self._btn_plein_ecran)

        btn_quitter = self._bouton_item(
            "  Quitter", style=_STYLE_DANGER, icone="exit.svg", couleur_icone=_CLR_DANGER
        )
        btn_quitter.clicked.connect(lambda: self.action_app_demande.emit("quit"))
        layout.addWidget(btn_quitter)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(
            f"background-color: {_BG}; border-bottom: 1px solid {_CLR_SEP};"
        )
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 4, 0)
        layout.setSpacing(0)

        titre = QLabel("Navigation")
        titre.setStyleSheet(
            f"color: {_CLR_TEXTE}; font-size: 13px; font-weight: 700; border: none;"
        )
        layout.addWidget(titre, 1)

        btn_fermer = QPushButton("✕")
        btn_fermer.setFixedSize(44, 44)
        btn_fermer.setStyleSheet(_STYLE_FERMER)
        btn_fermer.clicked.connect(self.fermeture_demandee.emit)
        layout.addWidget(btn_fermer)

        return header

    def _bouton_item(
        self,
        label: str,
        checkable: bool = False,
        style: str = _STYLE_ITEM,
        icone: str | None = None,
        couleur_icone: str = _CLR_TEXTE,
    ) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(checkable)
        btn.setStyleSheet(style)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFixedHeight(_HAUTEUR_ITEM)
        if icone:
            btn.setIcon(icone_coloree(icone, couleur_icone, _ICON_SIZE))
            btn.setIconSize(_ICON_SIZE)
        return btn

    def _separateur(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {_CLR_SEP}; border: none;")
        return sep

    def _naviguer(self, page_id: str):
        self.maj_page_active(page_id)
        self.page_demandee.emit(page_id)
        self.fermeture_demandee.emit()
