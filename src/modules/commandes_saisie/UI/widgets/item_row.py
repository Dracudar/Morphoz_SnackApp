#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
item_row.py

Description:
    Widget ligne d'article affichant un item dans la liste de commande en cours.

Author :
    Dracudar

Version:
    2.2

Date de création :
    2026.05.31

Date de modification:
    2026.06.21
"""

from typing import Dict
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from src.UI.utils.icones import icone_action
from src.backend.app_config import get_assets_path


ROW_HEIGHT = 48

# Stylesheets
CANCEL_BUTTON_STYLE = """
    QPushButton {
        background-color: #d9534f;
        border: 1px solid #ac2925;
        border-radius: 7px;
        padding: 0px;
    }
    QPushButton:hover { background-color: #c9302c; }
"""


def _make_cancel_icon(size: int = 26) -> QIcon:
    """Charge cancel.svg et retourne un QIcon avec modes normal (blanc) et désactivé (gris)."""
    def _colorize(color: str) -> QPixmap:
        renderer = QSvgRenderer(get_assets_path("icons", "cancel.svg"))
        raw = QPixmap(size, size)
        raw.fill(Qt.transparent)
        p = QPainter(raw)
        renderer.render(p)
        p.end()
        result = QPixmap(size, size)
        result.fill(Qt.transparent)
        p2 = QPainter(result)
        p2.drawPixmap(0, 0, raw)
        p2.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p2.fillRect(result.rect(), QColor(color))
        p2.end()
        return result

    icon = QIcon()
    icon.addPixmap(_colorize("white"), QIcon.Mode.Normal)
    icon.addPixmap(_colorize("#595d64"), QIcon.Mode.Disabled)
    return icon

ITEM_ROW_STYLE = """
    QFrame#itemRow {
        background-color: #3b3f46;
        border: 1px solid #60646c;
        border-radius: 4px;
        padding: 2px;
    }
"""

ITEM_LABEL_STYLE = """
    color: #f5f5f5;
    font-size: 13px;
    padding: 0 4px;
"""

ID_TYPE_LABEL_STYLE = """
    color: #f0b429;
    font-size: 14px;
    font-weight: 700;
    padding: 0 4px;
"""


def extract_plat_sort_key(item_id: str) -> tuple:
    """
    Retourne (type_prefix, numero) pour trier par type alphabétique puis numéro croissant.
    Ex: '20260606-007-P030' → ('P', 30),  '20260606-007-G001' → ('G', 1)
    """
    part = item_id.split("-")[-1] if "-" in item_id else item_id
    if part and len(part) > 1 and part[0].isalpha():
        try:
            return (part[0], int(part[1:]))
        except ValueError:
            pass
    return ("", 0)


class ItemRow(QFrame):
    """Ligne d'article : [Annuler ✕] [X000] [Nom du plat] [Prix]"""

    item_cancelled = Signal(str)  # Emits item_id

    def __init__(self, item_id: str, item_data: Dict, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.item_data = item_data
        self._build_ui()

    def _build_ui(self):
        """Construit la ligne : [Annuler] [X000] [Plat] [Prix]"""
        self.setFixedHeight(ROW_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(8)

        # Cancel button (left)
        cancel_btn = QPushButton()
        cancel_btn.setIcon(icone_action("cancel.svg", 26, "white", "#595d64"))
        cancel_btn.setIconSize(QSize(26, 26))
        cancel_btn.setFixedSize(36, 36)
        cancel_btn.setStyleSheet(CANCEL_BUTTON_STYLE)
        cancel_btn.clicked.connect(lambda: self.item_cancelled.emit(self.item_id))
        layout.addWidget(cancel_btn)

        # Identifiant de type journalier (P030, G001…) extrait depuis l'ID complet
        full_id = self.item_data.get("id", "")
        id_type = full_id.split("-")[-1] if "-" in full_id else ""
        id_type_label = QLabel(id_type or "—")
        id_type_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
        id_type_label.setFixedWidth(52)
        id_type_label.setStyleSheet(ID_TYPE_LABEL_STYLE)
        layout.addWidget(id_type_label)

        # Dish name (stretch)
        name = self.item_data.get("nom") or self.item_data.get("plat", "")
        details = QLabel(name)
        details.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        details.setStyleSheet(ITEM_LABEL_STYLE)
        layout.addWidget(details, 1)

        # Price (right-aligned)
        price_label = QLabel(f"{self.item_data['price']:.2f} €")
        price_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        price_label.setStyleSheet(ITEM_LABEL_STYLE)
        layout.addWidget(price_label)

        self.setObjectName("itemRow")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(ITEM_ROW_STYLE)
