#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
item_row.py

Description:
    Widget ligne d'article affichant un item dans la liste de commande en cours.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.05.31

Date de modification:
    2026.06.03
"""

from typing import Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


ROW_HEIGHT = 48

# Stylesheets
CANCEL_BUTTON_STYLE = """
    QPushButton {
        background-color: #d9534f;
        color: white;
        border: 1px solid #ac2925;
        border-radius: 4px;
        padding: 4px 8px;
        font-weight: 600;
        font-size: 14px;
    }
    QPushButton:hover { background-color: #c9302c; }
"""

ITEM_ROW_STYLE = """
    QFrame {
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

SEQ_LABEL_STYLE = """
    color: #a0a4ab;
    font-size: 12px;
    font-weight: 600;
    padding: 0 4px;
"""


def extract_seq(item_id: str) -> int:
    """Extrait le numéro de séquence depuis un ID de plat (ex: '20260603-001-02' → 2)."""
    part = item_id.split("-")[-1] if "-" in item_id else item_id.lstrip("#")
    try:
        return int(part)
    except ValueError:
        return 0


class ItemRow(QFrame):
    """Ligne d'article : [Annuler ✕] [#N] [Nom du plat] [Prix]"""

    item_cancelled = Signal(str)  # Emits item_id

    def __init__(self, item_id: str, item_data: Dict, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.item_data = item_data
        self._build_ui()

    def _build_ui(self):
        """Construit la ligne : [Annuler] [#N] [Plat] [Prix]"""
        self.setFixedHeight(ROW_HEIGHT)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(8)

        # Cancel button (left)
        cancel_btn = QPushButton("✕")
        cancel_btn.setFixedWidth(36)
        cancel_btn.setStyleSheet(CANCEL_BUTTON_STYLE)
        cancel_btn.clicked.connect(lambda: self.item_cancelled.emit(self.item_id))
        layout.addWidget(cancel_btn)

        # Sequence number (#N)
        seq = extract_seq(self.item_data.get("id", ""))
        seq_label = QLabel(f"#{seq}")
        seq_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
        seq_label.setFixedWidth(28)
        seq_label.setStyleSheet(SEQ_LABEL_STYLE)
        layout.addWidget(seq_label)

        # Dish name (stretch)
        name = self.item_data.get("plat") or self.item_data.get("nom", "")
        details = QLabel(name)
        details.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        details.setStyleSheet(ITEM_LABEL_STYLE)
        layout.addWidget(details, 1)

        # Price (right-aligned)
        price_label = QLabel(f"{self.item_data['price']:.2f} €")
        price_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        price_label.setStyleSheet(ITEM_LABEL_STYLE)
        layout.addWidget(price_label)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(ITEM_ROW_STYLE)
