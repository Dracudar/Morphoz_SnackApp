#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
panneau_lateral.py - Volet latéral du poste de préparation allégé

Description:
    Panneau de configuration minimal pour les postes de préparation :
    sélection du dossier data partagé en LAN, basculer en plein écran, quitter.
    Les boutons sont dimensionnés pour une utilisation tactile.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.14

Date de modification:
    2026.06.14
"""

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.backend.app_config import CONFIG_FILE, get_data_folder


_BG = "#23252a"

_BTN_BASE = (
    "QPushButton {"
    "  background-color: #4f545e; color: #f5f5f5;"
    "  border: none; border-radius: 6px;"
    "  padding: 14px 10px; font-size: 14px;"
    "}"
    "QPushButton:hover { background-color: #5a606b; }"
    "QPushButton:pressed { background-color: #3a3d43; }"
)

_BTN_PRIMARY = (
    "QPushButton {"
    "  background-color: #4a7fcb; color: #ffffff;"
    "  border: none; border-radius: 6px;"
    "  padding: 14px 10px; font-size: 14px; font-weight: 700;"
    "}"
    "QPushButton:hover { background-color: #5a8fdb; }"
    "QPushButton:pressed { background-color: #3a6fbb; }"
    "QPushButton:disabled { background-color: #2f3540; color: #6a7080; }"
)

_BTN_DANGER = (
    "QPushButton {"
    "  background-color: #c0392b; color: #f5f5f5;"
    "  border: none; border-radius: 6px;"
    "  padding: 14px 10px; font-size: 14px; font-weight: 700;"
    "}"
    "QPushButton:hover { background-color: #e74c3c; }"
    "QPushButton:pressed { background-color: #a93226; }"
)


class PanneauLateral(QWidget):
    """Volet latéral minimal : dossier data, plein écran, quitter."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self._main_window = main_window
        self.setFixedWidth(220)
        self.setStyleSheet(f"background-color: {_BG};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 16)
        layout.setSpacing(10)

        # Titre
        titre = QLabel("Poste\nPréparation")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet(
            f"color: #f5f5f5; font-size: 16px; font-weight: 700; background-color: {_BG};"
        )
        layout.addWidget(titre)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #3a3d43;")
        layout.addWidget(sep)

        # Section dossier data
        lbl_section = QLabel("Dossier data")
        lbl_section.setStyleSheet(f"color: #a8acb3; font-size: 12px; background-color: {_BG};")
        layout.addWidget(lbl_section)

        self._path_edit = QLineEdit(str(get_data_folder()))
        self._path_edit.setReadOnly(True)
        self._path_edit.setToolTip(self._path_edit.text())
        self._path_edit.setStyleSheet(
            "QLineEdit {"
            f"  background-color: #2f3136; color: #d6d6d6;"
            "  border: 1px solid #60646c; border-radius: 4px;"
            "  padding: 6px 8px; font-size: 11px;"
            "}"
        )
        layout.addWidget(self._path_edit)

        btn_parcourir = QPushButton("Parcourir…")
        btn_parcourir.setStyleSheet(_BTN_BASE)
        btn_parcourir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_parcourir.clicked.connect(self._choisir_dossier)
        layout.addWidget(btn_parcourir)

        self._btn_appliquer = QPushButton("Appliquer")
        self._btn_appliquer.setStyleSheet(_BTN_PRIMARY)
        self._btn_appliquer.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_appliquer.setEnabled(False)
        self._btn_appliquer.clicked.connect(self._appliquer_dossier)
        layout.addWidget(self._btn_appliquer)

        self._lbl_status = QLabel("")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setWordWrap(True)
        self._lbl_status.setStyleSheet(f"font-size: 11px; background-color: {_BG};")
        layout.addWidget(self._lbl_status)

        layout.addStretch()

        # Plein écran
        btn_fs = QPushButton("⛶  Plein écran")
        btn_fs.setStyleSheet(_BTN_BASE)
        btn_fs.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fs.clicked.connect(self._main_window.toggle_fullscreen)
        layout.addWidget(btn_fs)

        # Quitter
        btn_quit = QPushButton("✕  Quitter")
        btn_quit.setStyleSheet(_BTN_DANGER)
        btn_quit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_quit.clicked.connect(self._main_window.close)
        layout.addWidget(btn_quit)

    def _choisir_dossier(self):
        """Ouvre un sélecteur de dossier et pré-remplit le champ."""
        dossier = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier data",
            self._path_edit.text(),
        )
        if dossier:
            self._path_edit.setText(dossier)
            self._path_edit.setToolTip(dossier)
            self._btn_appliquer.setEnabled(True)
            self._lbl_status.setText("")

    def _appliquer_dossier(self):
        """Persiste le nouveau chemin data dans config.json sans écraser les autres clés."""
        new_path = self._path_edit.text().strip()
        if not new_path:
            return
        try:
            config = {}
            if CONFIG_FILE.exists():
                with CONFIG_FILE.open("r", encoding="utf-8") as f:
                    config = json.load(f)
            config["data_folder"] = new_path
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with CONFIG_FILE.open("w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            self._btn_appliquer.setEnabled(False)
            self._lbl_status.setStyleSheet("color: #4caf50; font-size: 11px;")
            self._lbl_status.setText("✓ Appliqué\n(redémarrer pour recharger)")
        except OSError:
            self._lbl_status.setStyleSheet("color: #e74c3c; font-size: 11px;")
            self._lbl_status.setText("Erreur d'écriture")
