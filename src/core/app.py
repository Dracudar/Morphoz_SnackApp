#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py

Description:
    Point d'entrée principal de l'application Morphoz SnackApp.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.18

Date de modification:
    2026.05.18
"""

from PySide6.QtWidgets import QApplication
from src.UI.main_window import MainWindow

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

