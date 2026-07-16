#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
launcher_window.py - Fenêtre de choix du mode de démarrage

Description:
    Point d'entrée unique de l'exécutable : propose 3 modes de démarrage
    (Saisie/Gestion, Poste de préparation, Historique/Statistiques) sans
    multiplier les builds PyInstaller. L'utilisateur choisit à chaque
    lancement — le choix n'est pas mémorisé.

    Permet aussi de choisir le dossier data avant d'ouvrir un mode : les
    fenêtres principales sont alors construites directement avec le bon
    dossier (carte, stock, historique) au lieu du dernier dossier utilisé.
    Ceci évite en particulier que le poste de préparation construise ses
    boutons filtre depuis une carte active périmée : ils ne sont jamais
    retirés une fois créés, donc un changement de dossier après coup, depuis
    le volet de la fenêtre déjà ouverte, laisse les anciens boutons affichés.

Author :
    Dracudar

Version:
    1.3

Date de création :
    2026.07.05

Date de modification:
    2026.07.16
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.backend import file_io
from src.backend.app_config import (
    CONFIG_FILE,
    get_assets_path,
    get_data_folder_brut,
    initialiser_dossier_data,
)
from src.UI.utils.icones import icone_coloree

_BG        = "#1e2124"
_BG_CARTE  = "#2f3136"
_BORDER    = "#4a4e55"
_TEXT      = "#f5f5f5"
_TEXT_MUTED = "#a8acb3"
_ACCENT    = "#4a7fcb"

# (icône, titre, description, identifiant de mode)
_MODES = [
    (
        "saisie.svg",
        "Prise de commandes",
        "Prise de commande, stock, carte, historique, statistiques.",
        "complet",
    ),
    (
        "prepa.svg",
        "Poste de préparation",
        "Affichage cuisine plein écran des plats à préparer.",
        "prepa",
    ),
    (
        "log.svg",
        "Gestion et statistiques",
        "Consultation de l'historique des ventes et de log et export de rapports en PDF.",
        "stats",
    ),
]


class LauncherWindow(QMainWindow):
    """Fenêtre de choix du mode de démarrage, affichée à chaque lancement de l'exécutable."""

    mode_choisi = Signal(str)  # "complet" | "prepa" | "stats"

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Morphoz SnackApp — Choix du mode")
        self.setWindowIcon(QIcon(get_assets_path("imgs", "logo_snack.svg")))
        self.resize(640, 560)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background-color: {_BG};")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        logo = QLabel()
        logo.setPixmap(QIcon(get_assets_path("imgs", "MegaSnack.svg")).pixmap(QSize(220, 48)))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        titre = QLabel("Choisissez un mode de démarrage")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet(f"color: {_TEXT}; font-size: 18px; font-weight: 700;")
        layout.addWidget(titre)

        layout.addSpacing(8)

        for icone, titre_mode, description, mode_id in _MODES:
            layout.addWidget(self._build_carte_mode(icone, titre_mode, description, mode_id))

        layout.addWidget(self._build_section_dossier())

        layout.addStretch()
        self.setCentralWidget(central)

    def _build_section_dossier(self) -> QFrame:
        carte = QFrame()
        carte.setStyleSheet(
            f"""
            QFrame {{
                background-color: {_BG_CARTE};
                border: 1px solid {_BORDER};
                border-radius: 10px;
            }}
            """
        )
        layout = QVBoxLayout(carte)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        lbl_section = QLabel("DOSSIER DATA")
        lbl_section.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 1px; border: none;"
        )
        layout.addWidget(lbl_section)

        chemin_row = QHBoxLayout()
        chemin_row.setSpacing(8)

        self._chemin_edit = QLineEdit(get_data_folder_brut())
        self._chemin_edit.setReadOnly(True)
        self._chemin_edit.setPlaceholderText("Dossier par défaut (./data)")
        self._chemin_edit.setToolTip(self._chemin_edit.text())
        self._chemin_edit.setStyleSheet(
            "QLineEdit {"
            "  background-color: #3b3f46; color: #f5f5f5;"
            "  border: 1px solid #676d79; border-radius: 4px;"
            "  padding: 6px 8px; font-size: 12px;"
            "}"
        )
        chemin_row.addWidget(self._chemin_edit, 1)

        btn_parcourir = QPushButton("Parcourir…")
        btn_parcourir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_parcourir.setStyleSheet(
            "QPushButton {"
            "  background-color: #4f545e; color: #f5f5f5;"
            "  border: none; border-radius: 4px;"
            "  padding: 8px 12px; font-size: 12px;"
            "}"
            "QPushButton:hover { background-color: #5a606b; }"
        )
        btn_parcourir.clicked.connect(self._choisir_dossier)
        chemin_row.addWidget(btn_parcourir)

        self._btn_appliquer = QPushButton("Appliquer")
        self._btn_appliquer.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_appliquer.setEnabled(False)
        self._btn_appliquer.setStyleSheet(
            "QPushButton {"
            "  background-color: #4a7fcb; color: #ffffff;"
            "  border: none; border-radius: 4px;"
            "  padding: 8px 12px; font-size: 12px; font-weight: 700;"
            "}"
            "QPushButton:hover { background-color: #5a8fdb; }"
            "QPushButton:disabled { background-color: #2f3540; color: #6a7080; }"
        )
        self._btn_appliquer.clicked.connect(self._appliquer_dossier)
        chemin_row.addWidget(self._btn_appliquer)

        layout.addLayout(chemin_row)

        self._lbl_status = QLabel("")
        self._lbl_status.setStyleSheet("font-size: 11px; border: none;")
        layout.addWidget(self._lbl_status)

        return carte

    def _build_carte_mode(self, icone: str, titre: str, description: str, mode_id: str) -> QPushButton:
        carte = QPushButton()
        carte.setCursor(Qt.CursorShape.PointingHandCursor)
        carte.setMinimumHeight(90)
        carte.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {_BG_CARTE};
                border: 1px solid {_BORDER};
                border-radius: 10px;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{
                border-color: {_ACCENT};
                background-color: #363a42;
            }}
            """
        )
        carte.clicked.connect(lambda: self._choisir(mode_id))

        contenu = QFrame(carte)
        contenu.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        contenu.setStyleSheet("background: transparent; border: none;")
        row = QHBoxLayout(contenu)
        row.setContentsMargins(18, 14, 18, 14)
        row.setSpacing(16)

        icone_label = QLabel()
        icone_label.setPixmap(icone_coloree(icone, _ACCENT, QSize(36, 36)).pixmap(QSize(36, 36)))
        icone_label.setFixedSize(36, 36)
        row.addWidget(icone_label)

        texte_layout = QVBoxLayout()
        texte_layout.setSpacing(2)
        titre_label = QLabel(titre)
        titre_label.setStyleSheet(f"color: {_TEXT}; font-size: 16px; font-weight: 700;")
        description_label = QLabel(description)
        description_label.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
        description_label.setWordWrap(True)
        texte_layout.addWidget(titre_label)
        texte_layout.addWidget(description_label)
        row.addLayout(texte_layout, 1)

        outer = QVBoxLayout(carte)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(contenu)

        return carte

    def _choisir(self, mode_id: str):
        self.mode_choisi.emit(mode_id)
        self.close()

    # ── Dossier data ─────────────────────────────────────────────────────────

    def _choisir_dossier(self):
        """Ouvre un sélecteur de dossier et pré-remplit le champ."""
        dossier = QFileDialog.getExistingDirectory(
            self, "Sélectionner le dossier data", self._chemin_edit.text(),
        )
        if dossier:
            self._chemin_edit.setText(dossier)
            self._chemin_edit.setToolTip(dossier)
            self._btn_appliquer.setEnabled(True)
            self._lbl_status.setText("")

    def _appliquer_dossier(self):
        """
        Persiste le nouveau dossier data avant l'ouverture d'un mode.

        Crée aussi sa structure de fichiers si nécessaire (stock.json,
        carte_active.json, commandes/, logs/), pour qu'un mode ouvert juste
        après trouve un dossier déjà valide.
        """
        new_path = self._chemin_edit.text().strip()
        if not new_path:
            return
        try:
            with file_io.verrou_fichier(CONFIG_FILE):
                config = file_io.charger_json(CONFIG_FILE)
                config["data_folder"] = new_path
                file_io.sauvegarder_json(CONFIG_FILE, config)
            initialiser_dossier_data()
            self._btn_appliquer.setEnabled(False)
            self._lbl_status.setStyleSheet("color: #4caf50; font-size: 11px; border: none;")
            self._lbl_status.setText("✓ Appliqué")
        except OSError:
            self._lbl_status.setStyleSheet("color: #e74c3c; font-size: 11px; border: none;")
            self._lbl_status.setText("Erreur d'écriture")
