#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
payment_dialog.py

Description:
    Dialogue modal de sélection du mode de paiement.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.31

Date de modification:
    2026.05.31
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel


PAYMENT_BUTTON_STYLE = """
    QPushButton {
        background-color: #4f545e;
        border: 2px solid #7d8390;
        border-radius: 8px;
        padding: 10px;
    }
    QPushButton:hover {
        background-color: #626978;
        border: 2px solid #8fa3b6;
    }
    QPushButton:pressed {
        background-color: #3a3d43;
    }
"""


class PaymentDialog(QDialog):
    """Modal dialog for selecting payment method."""

    payment_selected = Signal(str)  # Emits: "Gratuit", "Carte", or "Espèces"

    def __init__(self, amount: float, parent=None):
        super().__init__(parent)
        self.amount = amount
        self.setWindowTitle("Mode de paiement")
        self.setModal(True)
        self.setFixedSize(400, 250)
        self._build_ui()

    def _build_ui(self):
        """Build dialog layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Sélectionnez le mode de paiement")
        title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f5f5f5;")
        layout.addWidget(title)

        # Payment buttons container (horizontal)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # Define payment options: (label, icon_path, payment_type)
        payments = [
            ("Gratuit", "assets/icons/free.svg", "Gratuit"),
            ("Carte", "assets/icons/card.svg", "Carte"),
            ("Espèces", "assets/icons/coin.svg", "Espèces"),
        ]

        for label, icon_path, payment_type in payments:
            btn = self._create_payment_button(label, icon_path, payment_type)
            buttons_layout.addWidget(btn)

        layout.addLayout(buttons_layout)
        layout.addStretch()

        # Amount display (bottom right)
        amount_label = QLabel(f"Total: {self.amount:.2f} €")
        amount_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_label.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #a8d08d;"
        )
        layout.addWidget(amount_label)

    def _create_payment_button(
        self, label: str, icon_path: str, payment_type: str
    ) -> QPushButton:
        """Create individual payment button with icon above text."""
        btn = QPushButton()

        # Layout: icon above text
        btn_layout = QVBoxLayout(btn)

        # Icon (SVG)
        icon_label = QLabel()
        pixmap = self._load_svg_icon(icon_path, size=50)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(icon_label)

        # Text
        text_label = QLabel(label)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("color: #f5f5f5; font-weight: 600;")
        btn_layout.addWidget(text_label)

        btn.setMinimumSize(100, 100)
        btn.setStyleSheet(PAYMENT_BUTTON_STYLE)
        btn.clicked.connect(lambda: self._on_payment_selected(payment_type))

        return btn

    def _load_svg_icon(self, svg_path: str, size: int = 50) -> QPixmap:
        """Load SVG icon and render to QPixmap."""
        try:
            engine = QSvgRenderer(svg_path)
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            engine.render(painter)
            painter.end()
            return pixmap
        except Exception:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.gray)
            return pixmap

    def _on_payment_selected(self, payment_type: str):
        """Emit selected payment type and close dialog."""
        self.payment_selected.emit(payment_type)
        self.accept()
