#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py

Description:
    Point d'entrée principal de l'application Morphoz SnackApp.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.05.18

Date de modification:
    2026.06.07
"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication
from src.UI.main_window import MainWindow


def _build_dark_palette() -> QPalette:
    """Construit et retourne la palette sombre de l'application."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(47, 49, 54))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Base, QColor(47, 49, 54))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(58, 61, 67))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(47, 49, 54))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Text, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.Button, QColor(79, 84, 94))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 100, 100))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(245, 245, 245))
    # Éléments désactivés
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(143, 148, 156))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(143, 148, 156))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(143, 148, 156))
    return palette


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(_build_dark_palette())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

