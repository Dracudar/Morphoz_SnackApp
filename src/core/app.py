#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window.py - Main Window Module

Description:
    Gate to Morphoz SnackApp.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.17

Date de modification:
    2026.05.17

License :
    MIT
"""

from PySide6.QtWidgets import QApplication
from src.UI.main_window import MainWindow

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

