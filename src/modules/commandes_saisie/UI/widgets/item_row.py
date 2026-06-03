#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
item_row.py

Description:
    Widget ligne d'article affichant un item dans la liste de commande en cours.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.31

Date de modification:
    2026.05.31
"""

from typing import Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


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
    QFrame:hover { background-color: #454b52; }
"""

ITEM_LABEL_STYLE = """
    color: #f5f5f5;
    font-size: 13px;
    padding: 4px;
"""


class ItemRow(QFrame):
    """Single item row: [Cancel X] [ID - Name] [Status] [Price]"""

    item_cancelled = Signal(str)  # Emits item_id

    def __init__(self, item_id: str, item_data: Dict, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.item_data = item_data
        self._build_ui()

    def _build_ui(self):
        """Build layout: [Cancel] [Details] [Status] [Price]"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        # Cancel button (left)
        cancel_btn = QPushButton("✕")
        cancel_btn.setMaximumWidth(50)
        cancel_btn.setStyleSheet(CANCEL_BUTTON_STYLE)
        cancel_btn.clicked.connect(lambda: self.item_cancelled.emit(self.item_id))
        layout.addWidget(cancel_btn)

        # Item details: ID - Name (stretch)
        details = QLabel(f"{self.item_data['id']} - {self.item_data['nom']}")
        details.setStyleSheet(ITEM_LABEL_STYLE)
        layout.addWidget(details, 1)

        # Status (color-coded, fixed width)
        status_label = QLabel(self.item_data['status'])
        status_color = self._get_status_color(self.item_data['status'])
        status_label.setStyleSheet(f"color: {status_color}; font-weight: 600;")
        status_label.setMaximumWidth(120)
        layout.addWidget(status_label)

        # Price (right-aligned)
        price_label = QLabel(f"{self.item_data['price']:.2f} €")
        price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(price_label)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(ITEM_ROW_STYLE)

    def _get_status_color(self, status: str) -> str:
        """Return color based on item status."""
        status_lower = status.lower()
        if "attente" in status_lower:
            return "#ffd700"      # Yellow - waiting
        elif "préparation" in status_lower:
            return "#00bfff"      # Blue - in prep
        elif "livré" in status_lower:
            return "#90ee90"      # Green - delivered
        elif "annulé" in status_lower:
            return "#ff6b6b"      # Red - cancelled
        return "#d6d6d6"          # Default - gray
