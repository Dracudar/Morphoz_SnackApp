#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loading_window.py - Fenêtre de chargement intermédiaire

Description:
    Petite fenêtre affichée pendant la construction d'un mode depuis le
    launcher : l'import des dépendances lourdes (QtCharts, reportlab...) et
    la construction de la fenêtre principale sont synchrones et peuvent
    prendre une à quelques secondes, ce qui donnait une impression de gel de
    l'application sans aucun retour visuel. Affichée par session.lancer_mode()
    juste avant l'import, fermée juste après la construction de la fenêtre.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.16

Date de modification:
    2026.07.16
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

from src.backend.app_config import get_assets_path

_BG     = "#1e2124"
_BORDER = "#4a4e55"
_TEXT   = "#f5f5f5"
_ACCENT = "#4a7fcb"


class FenetreChargement(QWidget):
    """Petite fenêtre sans bordure affichée pendant la construction d'un mode."""

    def __init__(self, texte: str = "Chargement…"):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowIcon(QIcon(get_assets_path("imgs", "logo_snack.svg")))
        self.setFixedSize(300, 150)
        self.setStyleSheet(
            f"background-color: {_BG}; border: 1px solid {_BORDER}; border-radius: 10px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        logo = QLabel()
        logo.setPixmap(QIcon(get_assets_path("imgs", "MegaSnack.svg")).pixmap(QSize(160, 34)))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        label = QLabel(texte)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"color: {_TEXT}; font-size: 13px;")
        layout.addWidget(label)

        barre = QProgressBar()
        barre.setRange(0, 0)  # indéterminée : juste une animation de patience
        barre.setTextVisible(False)
        barre.setFixedHeight(8)
        barre.setStyleSheet(
            "QProgressBar { background-color: #2f3136; border: none; border-radius: 4px; }"
            f"QProgressBar::chunk {{ background-color: {_ACCENT}; border-radius: 4px; }}"
        )
        layout.addWidget(barre)

        self._centrer()

    def _centrer(self):
        ecran = QGuiApplication.primaryScreen()
        if ecran is not None:
            centre = ecran.geometry().center()
            self.move(centre.x() - self.width() // 2, centre.y() - self.height() // 2)
