#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
panneau_lateral.py - Volet latéral du poste de préparation allégé

Description:
    Volet de configuration pour les postes de préparation : sélection du dossier
    data partagé en LAN, basculer en plein écran, quitter. S'affiche en
    superposition sur le contenu principal via un bouton hamburger dans la barre
    de navigation.

Author :
    Dracudar

Version:
    2.1

Date de création :
    2026.06.14

Date de modification:
    2026.06.19
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.backend import file_io
from src.backend.app_config import CONFIG_FILE, get_data_folder

# ── Palette ───────────────────────────────────────────────────────────────────
_BG          = "#1e2124"
_BG_HOVER    = "#2c2f33"
_CLR_TEXTE   = "#e8e8e8"
_CLR_SEP     = "#36393f"
_HAUTEUR_ITEM = 50

_STYLE_ITEM = f"""
    QPushButton {{
        background-color: {_BG};
        color: {_CLR_TEXTE};
        border: none;
        text-align: left;
        padding: 0 20px;
        font-size: 14px;
        min-height: {_HAUTEUR_ITEM}px;
    }}
    QPushButton:hover {{ background-color: {_BG_HOVER}; }}
    QPushButton:checked {{ background-color: #4a7fcb; font-weight: 700; }}
"""

_STYLE_DANGER = f"""
    QPushButton {{
        background-color: {_BG};
        color: #e05c5c;
        border: none;
        text-align: left;
        padding: 0 20px;
        font-size: 14px;
        min-height: {_HAUTEUR_ITEM}px;
    }}
    QPushButton:hover {{ background-color: #3a1e1e; }}
"""

_STYLE_FERMER = f"""
    QPushButton {{
        color: #999;
        background: transparent;
        border: none;
        font-size: 18px;
    }}
    QPushButton:hover {{ color: {_CLR_TEXTE}; background-color: {_BG_HOVER}; }}
"""


class VoletPrep(QFrame):
    """Volet de configuration latéral pour le poste de préparation (superposition dynamique)."""

    action_app_demande = Signal(str)  # "fullscreen" | "quit"
    dossier_applique   = Signal()     # nouveau dossier data persisté → demande un refresh

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self._btn_plein_ecran: QPushButton | None = None
        self._build_ui()
        self.hide()

    # ── API publique ──────────────────────────────────────────────────────────

    def maj_etat_plein_ecran(self, actif: bool):
        """Met à jour le libellé et l'état coché du bouton plein écran."""
        if self._btn_plein_ecran:
            self._btn_plein_ecran.setChecked(actif)
            self._btn_plein_ecran.setText(
                "⛶  Quitter plein écran" if actif else "⛶  Plein écran"
            )

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"QFrame {{ background-color: {_BG}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_section_data())
        layout.addWidget(self._separateur())
        layout.addStretch(1)
        layout.addWidget(self._separateur())

        self._btn_plein_ecran = self._bouton_item("⛶  Plein écran", checkable=True)
        self._btn_plein_ecran.clicked.connect(
            lambda: self.action_app_demande.emit("fullscreen")
        )
        layout.addWidget(self._btn_plein_ecran)

        btn_quitter = self._bouton_item("✕  Quitter", style=_STYLE_DANGER)
        btn_quitter.clicked.connect(lambda: self.action_app_demande.emit("quit"))
        layout.addWidget(btn_quitter)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(
            f"background-color: {_BG}; border-bottom: 1px solid {_CLR_SEP};"
        )
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 4, 0)
        layout.setSpacing(0)

        titre = QLabel("Paramètres")
        titre.setStyleSheet(
            f"color: {_CLR_TEXTE}; font-size: 13px; font-weight: 700; border: none;"
        )
        layout.addWidget(titre, 1)

        btn_fermer = QPushButton("✕")
        btn_fermer.setFixedSize(44, 44)
        btn_fermer.setStyleSheet(_STYLE_FERMER)
        btn_fermer.clicked.connect(self.hide)
        layout.addWidget(btn_fermer)

        return header

    def _build_section_data(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f"background-color: {_BG};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        lbl_section = QLabel("DOSSIER DATA PARTAGÉ")
        lbl_section.setStyleSheet(
            "color: #a8acb3; font-size: 10px; font-weight: 700; letter-spacing: 1px;"
        )
        layout.addWidget(lbl_section)

        self._path_edit = QLineEdit(str(get_data_folder()))
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
        self._lbl_status.setStyleSheet(f"font-size: 11px; background-color: {_BG};")
        layout.addWidget(self._lbl_status)

        return container

    def _bouton_item(self, label: str, checkable: bool = False, style: str = _STYLE_ITEM) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(checkable)
        btn.setStyleSheet(style)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFixedHeight(_HAUTEUR_ITEM)
        return btn

    def _separateur(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {_CLR_SEP}; border: none;")
        return sep

    # ── Actions ───────────────────────────────────────────────────────────────

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
