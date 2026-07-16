#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parametres_dossier.py - Paramètres légers réutilisables (dossier data)

Description:
    Composants de paramètres partagés par les modes allégés (Poste de
    préparation, Statistiques) : pour le moment uniquement le dossier data
    partagé en LAN. ParametresDossierWidget est la section réutilisable
    (chemin, parcourir, appliquer) ; PageParametresLegere l'encapsule dans
    une page complète (titre + bouton retour) affichable dans le
    QStackedWidget de contenu de chaque mode, au même titre que ses autres
    pages.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.16

Date de modification:
    2026.07.16
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.backend import file_io
from src.backend.app_config import CONFIG_FILE, get_data_folder_brut
from src.UI.utils.icones import icone

# ── Palette (identique aux pages historique/paramètres) ──────────────────────
_BG_MAIN     = "#2f3136"
_BORDER_CARD = "#7f7f7f"
_TEXT_TITLE  = "#f5f5f5"


class ParametresDossierWidget(QWidget):
    """Section réutilisable : chemin du dossier data partagé, avec parcourir/appliquer."""

    dossier_applique = Signal()  # nouveau dossier data persisté → demande un refresh

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl_section = QLabel("DOSSIER DATA PARTAGÉ")
        lbl_section.setStyleSheet(
            "color: #a8acb3; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        layout.addWidget(lbl_section)

        self._path_edit = QLineEdit(get_data_folder_brut())
        self._path_edit.setReadOnly(True)
        self._path_edit.setToolTip(self._path_edit.text())
        self._path_edit.setStyleSheet(
            "QLineEdit {"
            "  background-color: #2f3136; color: #d6d6d6;"
            "  border: 1px solid #60646c; border-radius: 4px;"
            "  padding: 6px 8px; font-size: 11px;"
            "}"
        )
        layout.addWidget(self._path_edit)

        btn_parcourir = QPushButton("Parcourir…")
        btn_parcourir.setStyleSheet(
            "QPushButton {"
            "  background-color: #4f545e; color: #f5f5f5;"
            "  border: none; border-radius: 4px;"
            "  padding: 8px 10px; font-size: 13px;"
            "}"
            "QPushButton:hover { background-color: #5a606b; }"
            "QPushButton:pressed { background-color: #3a3d43; }"
        )
        btn_parcourir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_parcourir.clicked.connect(self._choisir_dossier)
        layout.addWidget(btn_parcourir)

        self._btn_appliquer = QPushButton("Appliquer")
        self._btn_appliquer.setStyleSheet(
            "QPushButton {"
            "  background-color: #4a7fcb; color: #ffffff;"
            "  border: none; border-radius: 4px;"
            "  padding: 8px 10px; font-size: 13px; font-weight: 700;"
            "}"
            "QPushButton:hover { background-color: #5a8fdb; }"
            "QPushButton:pressed { background-color: #3a6fbb; }"
            "QPushButton:disabled { background-color: #2f3540; color: #6a7080; }"
        )
        self._btn_appliquer.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_appliquer.setEnabled(False)
        self._btn_appliquer.clicked.connect(self._appliquer_dossier)
        layout.addWidget(self._btn_appliquer)

        self._lbl_status = QLabel("")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setWordWrap(True)
        self._lbl_status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self._lbl_status)

    def _choisir_dossier(self):
        """Ouvre un sélecteur de dossier et pré-remplit le champ."""
        dossier = QFileDialog.getExistingDirectory(
            self, "Sélectionner le dossier data", self._path_edit.text(),
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
            with file_io.verrou_fichier(CONFIG_FILE):
                config = file_io.charger_json(CONFIG_FILE)
                config["data_folder"] = new_path
                file_io.sauvegarder_json(CONFIG_FILE, config)
            self._btn_appliquer.setEnabled(False)
            self._lbl_status.setStyleSheet("color: #4caf50; font-size: 11px;")
            self._lbl_status.setText("✓ Appliqué")
            self.dossier_applique.emit()
        except OSError:
            self._lbl_status.setStyleSheet("color: #e74c3c; font-size: 11px;")
            self._lbl_status.setText("Erreur d'écriture")


class PageParametresLegere(QFrame):
    """Page Paramètres légère (dossier data uniquement) pour les modes Préparation et Statistiques."""

    go_back = Signal()
    dossier_applique = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pageParametresLegere")
        self._build_ui()

    def _build_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        title = QLabel("Paramètres")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("sectionTitle")
        main_layout.addWidget(title)

        self._section = ParametresDossierWidget()
        self._section.dossier_applique.connect(self.dossier_applique.emit)
        main_layout.addWidget(self._section)

        main_layout.addStretch(1)

        back_button = QPushButton("  Retour")
        back_button.setObjectName("backButton")
        back_button.setIcon(icone("return.svg", 18))
        back_button.setIconSize(QSize(18, 18))
        back_button.clicked.connect(self.go_back.emit)
        main_layout.addWidget(back_button)

        self.setStyleSheet(
            f"""
            QFrame#pageParametresLegere {{
                background-color: {_BG_MAIN};
                border: 1px solid {_BORDER_CARD};
            }}
            QLabel#sectionTitle {{
                color: {_TEXT_TITLE};
                font-size: 22px;
                font-weight: 700;
                padding: 4px;
            }}
            QPushButton#backButton {{
                background-color: #4f545e;
                border: 1px solid #7d8390;
                border-radius: 7px;
                color: {_TEXT_TITLE};
                font-size: 14px;
                font-weight: 700;
                min-height: 38px;
                padding: 6px 12px;
            }}
            QPushButton#backButton:hover {{
                background-color: #626978;
            }}
            """
        )
