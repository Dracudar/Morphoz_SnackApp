#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launcher_window.py - Fenêtre de choix du mode de démarrage

Description:
    Point d'entrée unique de l'exécutable : propose 3 modes de démarrage
    (Saisie/Gestion, Poste de préparation, Historique/Statistiques) sans
    multiplier les builds PyInstaller. L'utilisateur choisit à chaque
    lancement — le choix n'est pas mémorisé.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.05

Date de modification:
    2026.07.05
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.backend.app_config import get_assets_path
from src.UI.utils.icones import icone_coloree

_BG        = "#1e2124"
_BG_CARTE  = "#2f3136"
_BORDER    = "#4a4e55"
_TEXT      = "#f5f5f5"
_TEXT_MUTED = "#a8acb3"
_ACCENT    = "#4a7fcb"

# (icône, titre, description, identifiant de mode)
_MODES = [
    (
        "saisie.svg",
        "Saisie / Gestion",
        "Prise de commande, stock, carte, historique, statistiques, paramètres, journal.",
        "complet",
    ),
    (
        "prepa.svg",
        "Poste de préparation",
        "Affichage cuisine plein écran des plats à préparer.",
        "prepa",
    ),
    (
        "historique.svg",
        "Historique / Statistiques",
        "Consultation de l'historique des ventes et export de rapports en PDF.",
        "stats",
    ),
]


class LauncherWindow(QMainWindow):
    """Fenêtre de choix du mode de démarrage, affichée à chaque lancement de l'exécutable."""

    mode_choisi = Signal(str)  # "complet" | "prepa" | "stats"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Morphoz SnackApp — Choix du mode")
        self.setWindowIcon(QIcon(get_assets_path("imgs", "logo_snack.svg")))
        self.resize(640, 560)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {_BG};")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        logo = QLabel()
        logo.setPixmap(QIcon(get_assets_path("imgs", "MegaSnack.svg")).pixmap(QSize(220, 48)))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        titre = QLabel("Choisissez un mode de démarrage")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet(f"color: {_TEXT}; font-size: 18px; font-weight: 700;")
        layout.addWidget(titre)

        layout.addSpacing(8)

        for icone, titre_mode, description, mode_id in _MODES:
            layout.addWidget(self._build_carte_mode(icone, titre_mode, description, mode_id))

        layout.addStretch()
        self.setCentralWidget(central)

    def _build_carte_mode(self, icone: str, titre: str, description: str, mode_id: str) -> QPushButton:
        carte = QPushButton()
        carte.setCursor(Qt.CursorShape.PointingHandCursor)
        carte.setMinimumHeight(90)
        carte.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {_BG_CARTE};
                border: 1px solid {_BORDER};
                border-radius: 10px;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{
                border-color: {_ACCENT};
                background-color: #363a42;
            }}
            """
        )
        carte.clicked.connect(lambda: self._choisir(mode_id))

        contenu = QFrame(carte)
        contenu.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        contenu.setStyleSheet("background: transparent; border: none;")
        row = QHBoxLayout(contenu)
        row.setContentsMargins(18, 14, 18, 14)
        row.setSpacing(16)

        icone_label = QLabel()
        icone_label.setPixmap(icone_coloree(icone, _ACCENT, QSize(36, 36)).pixmap(QSize(36, 36)))
        icone_label.setFixedSize(36, 36)
        row.addWidget(icone_label)

        texte_layout = QVBoxLayout()
        texte_layout.setSpacing(2)
        titre_label = QLabel(titre)
        titre_label.setStyleSheet(f"color: {_TEXT}; font-size: 16px; font-weight: 700;")
        description_label = QLabel(description)
        description_label.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
        description_label.setWordWrap(True)
        texte_layout.addWidget(titre_label)
        texte_layout.addWidget(description_label)
        row.addLayout(texte_layout, 1)

        outer = QVBoxLayout(carte)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(contenu)

        return carte

    def _choisir(self, mode_id: str):
        self.mode_choisi.emit(mode_id)
        self.close()
