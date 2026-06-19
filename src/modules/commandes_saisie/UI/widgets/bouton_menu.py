#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bouton_menu.py

Description:
    Widget bouton menu carré avec icône SVG et libellé de catégorie de plat.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.05.18

Date de modification:
    2026.06.19
"""

import unicodedata
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QLabel

from src.backend.app_config import PROJECT_ROOT, get_assets_path
from src.backend import logger


BOUTON_MENU_STYLE = """
    QPushButton {
        background-color: #3b3f46;
        border: 2px solid #60646c;
        border-radius: 8px;
        padding: 8px;
    }
    QPushButton:hover {
        background-color: #454b52;
        border: 2px solid #7d8390;
    }
    QPushButton:pressed {
        background-color: #505660;
    }
"""


class BoutonMenu(QPushButton):
    """Bouton carré de menu avec icône SVG et libellé de catégorie en dessous."""

    def __init__(
        self, category_name: str, svg_path: Optional[str] = None, parent=None
    ):
        super().__init__(parent)
        self.category_name = category_name
        self.svg_path = svg_path or self._get_default_svg()
        self.setFixedSize(120, 120)  # Square button
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()

    def _build_ui(self):
        """Construit la mise en page : icône SVG centrée + libellé de catégorie."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Icon (SVG centered)
        icon_label = QLabel()
        icon_pixmap = self._load_svg_icon(self.svg_path, size=80)
        icon_label.setPixmap(icon_pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label, 1)

        # Category name (centered, wrapped)
        name_label = QLabel(self.category_name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #f5f5f5;"
        )
        layout.addWidget(name_label)

        self.setStyleSheet(BOUTON_MENU_STYLE)

    def _get_default_svg(self) -> str:
        """Recherche l'icône SVG dans le dossier du plat, ou retourne l'icône vide par défaut."""
        # Format: "Pizza" -> "pizza" or "Salade composée" -> "salade_composee"
        normalized = unicodedata.normalize("NFD", self.category_name)
        ascii_name = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        plat_name_lower = ascii_name.lower().replace(" ", "_")
        category_folder = PROJECT_ROOT / "src" / "modules" / "plats" / plat_name_lower
        category_icon = category_folder / "icon.svg"

        if category_icon.exists():
            return str(category_icon)
        return get_assets_path("icons", "void.svg")

    def _load_svg_icon(self, svg_path: str, size: int = 80) -> QPixmap:
        """Charge et rastérise un fichier SVG en QPixmap de la taille donnée."""
        try:
            engine = QSvgRenderer(svg_path)
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            engine.render(painter)
            painter.end()
            return pixmap
        except Exception as e:
            logger.log(logger.ERREUR, {
                "contexte": "bouton_menu_chargement_svg",
                "type_erreur": type(e).__name__,
                "message": str(e),
                "chemin_svg": svg_path,
            })
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.gray)
            return pixmap
