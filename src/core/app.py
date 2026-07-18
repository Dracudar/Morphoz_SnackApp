#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py

Description:
    Point d'entrée unique de l'application Morphoz SnackApp. Affiche d'abord
    LauncherWindow, qui laisse choisir l'un des 3 modes de démarrage (Saisie/
    Gestion, Poste de préparation, Historique/Statistiques) — un seul
    exécutable, pas de build ni de release séparés par mode.

Author :
    Dracudar

Version:
    2.1

Date de création :
    2026.05.18

Date de modification:
    2026.07.16
"""

from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication


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
    import os
    import sys

    # Sur Linux, forcer XCB (XWayland) pour contourner le crash Qt 6.8.0
    # dans zwp_text_input_v3 sur Wayland — corrigé dans Qt 6.8.1+
    if sys.platform == "linux":
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    from src.backend import app_config, logger, update_checker
    from src.core import session

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(_build_dark_palette())
    app.setWindowIcon(QIcon(app_config.get_assets_path("imgs", "logo_snack.svg")))

    # Crée le dossier data et ses fichiers JSON vides si absents (premier lancement)
    app_config.initialiser_dossier_data()

    logger.log(logger.DEMARRAGE_APP, {})
    app.aboutToQuit.connect(lambda: logger.log(logger.ARRET_APP, {}))
    # Attend la fin des vérifications de mise à jour encore en cours (sinon Qt peut
    # planter en détruisant un fil de vérification pendant qu'il tourne encore).
    app.aboutToQuit.connect(lambda: update_checker.attendre_verifications_en_cours())

    # session.ouvrir_launcher() garde une référence forte sur la fenêtre créée
    # (sinon garbage collectée faute de variable locale conservée) ; le même
    # mécanisme permet d'ouvrir plusieurs fenêtres simultanément (ex. revenir
    # au launcher ou en ouvrir une session supplémentaire depuis un mode).
    session.ouvrir_launcher()

    sys.exit(app.exec())

