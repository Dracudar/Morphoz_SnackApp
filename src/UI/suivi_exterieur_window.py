#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suivi_exterieur_window.py - Fenêtre de suivi extérieur

Description:
    Fenêtre indépendante (lecture seule) destinée à l'affichage public des commandes.
    Montre les plats prêts à récupérer et les prochains plats en préparation
    (2 au maximum par type). Aucune interaction possible.
    Peut être déplacée sur un écran secondaire et mise en plein écran indépendamment.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.06.08

Date de modification:
    2026.06.10
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.backend.data_sources import get_live_orders_prep

# Nombre maximum de plats "En préparation" affichés par type
_MAX_EN_PREP_PAR_TYPE = 2

# ── Palette ──────────────────────────────────────────────────────────────────
_BG             = "#23262b"
_BG_SECTION     = "#2f3136"
_BG_PRET        = "#1a2e1a"
_BG_PREP        = "#2e1f0a"
_BORDER_PRET    = "#4caf50"
_BORDER_PREP    = "#c97a30"
_TEXT_TITRE     = "#f5f5f5"
_TEXT_SECTION   = "#d6d6d6"
_TEXT_ID        = "#ffffff"
_TEXT_TYPE      = "#a8acb3"
_TEXT_VIDE      = "#555a63"

_STYLE_PRET = f"color: #4caf50; font-size: 14px; font-weight: 700;"
_STYLE_PREP = f"color: #c97a30; font-size: 14px; font-weight: 700;"


class SuiviExterieurWindow(QMainWindow):
    """Fenêtre publique de suivi des commandes, sans interaction."""

    # Émis quand l'utilisateur ferme la fenêtre via le bouton × (elle se masque, ne se détruit pas)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Suivi des commandes")
        self.setGeometry(200, 200, 800, 600)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._build_ui()
        self._setup_shortcuts()
        self._build_timer()
        self.refresh()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        root.setStyleSheet(f"background-color: {_BG};")
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(16)

        # Titre
        titre = QLabel("Suivi des commandes")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titre.setStyleSheet(
            f"color: {_TEXT_TITRE}; font-size: 26px; font-weight: 700; padding: 8px 0;"
        )
        main_layout.addWidget(titre)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            f"QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: {_BG}; }}"
        )
        main_layout.addWidget(scroll)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(16)
        self._content_layout.addStretch()
        scroll.setWidget(self._content)

    def _setup_shortcuts(self):
        fs_action = QAction(self)
        fs_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        fs_action.triggered.connect(self._toggle_fullscreen)
        self.addAction(fs_action)

        esc_action = QAction(self)
        esc_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        esc_action.triggered.connect(self._exit_fullscreen)
        self.addAction(esc_action)

    def _build_timer(self):
        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def force_close(self):
        """Ferme définitivement la fenêtre lors de la fermeture de l'application."""
        self._timer.stop()
        self._app_closing = True
        self.close()

    def closeEvent(self, event):
        """Masque la fenêtre (fermeture manuelle) ou la détruit (fermeture de l'app)."""
        if getattr(self, '_app_closing', False):
            event.accept()
            return
        event.ignore()
        self.hide()
        self.closed.emit()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

    # ── Données ───────────────────────────────────────────────────────────────

    def _clear_content(self):
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh(self):
        """Recharge les plats depuis le disque et reconstruit l'affichage."""
        plats = get_live_orders_prep()

        prêts   = [p for p in plats if p["status"].lower() == "prêt"]
        en_prep = [p for p in plats if p["status"].lower() == "en préparation"]

        # Regrouper les plats en préparation par type, garder les 2 premiers par type
        prep_par_type: dict[str, list[dict]] = {}
        for plat in en_prep:
            t = plat["plat"]
            prep_par_type.setdefault(t, [])
            if len(prep_par_type[t]) < _MAX_EN_PREP_PAR_TYPE:
                prep_par_type[t].append(plat)

        self._clear_content()

        # Section "Prêts"
        self._content_layout.insertWidget(
            self._content_layout.count() - 1,
            self._build_section_prêts(prêts),
        )

        # Section "En préparation"
        self._content_layout.insertWidget(
            self._content_layout.count() - 1,
            self._build_section_prep(prep_par_type),
        )

    # ── Construction des sections ──────────────────────────────────────────────

    def _build_section_prêts(self, prêts: list[dict]) -> QFrame:
        section = self._make_section_frame(_BG_PRET, _BORDER_PRET)
        layout = section.layout()

        titre = QLabel("✓  Prêts à récupérer")
        titre.setStyleSheet(f"color: #4caf50; font-size: 18px; font-weight: 700;")
        layout.addWidget(titre)

        if not prêts:
            vide = QLabel("Aucune commande prête pour le moment")
            vide.setStyleSheet(f"color: {_TEXT_VIDE}; font-size: 15px; font-style: italic;")
            layout.addWidget(vide)
        else:
            for plat in prêts:
                layout.addWidget(self._build_plat_row(plat, _STYLE_PRET))

        return section

    def _build_section_prep(self, prep_par_type: dict[str, list[dict]]) -> QFrame:
        section = self._make_section_frame(_BG_PREP, _BORDER_PREP)
        layout = section.layout()

        titre = QLabel("⏳  En préparation")
        titre.setStyleSheet(f"color: #c97a30; font-size: 18px; font-weight: 700;")
        layout.addWidget(titre)

        if not prep_par_type:
            vide = QLabel("Aucun plat en cours de préparation")
            vide.setStyleSheet(f"color: {_TEXT_VIDE}; font-size: 15px; font-style: italic;")
            layout.addWidget(vide)
        else:
            for plat_type, plats in prep_par_type.items():
                for plat in plats:
                    layout.addWidget(self._build_plat_row(plat, _STYLE_PREP))

        return section

    def _make_section_frame(self, bg: str, border_color: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border: 1px solid {border_color}; border-radius: 10px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        return frame

    def _build_plat_row(self, plat: dict, label_style: str) -> QWidget:
        """Construit une ligne affichant le type et l'ID court (numéro de commande) d'un plat."""
        row = QWidget()
        row.setStyleSheet("QWidget { background: transparent; border: none; }")
        h = QHBoxLayout(row)
        h.setContentsMargins(4, 2, 4, 2)
        h.setSpacing(16)

        # Type du plat
        type_label = QLabel(plat["plat"])
        type_label.setFixedWidth(160)
        type_label.setStyleSheet(f"color: {_TEXT_TYPE}; font-size: 15px; border: none;")
        h.addWidget(type_label)

        # Numéro de commande (partie centrale de l'ID, ex. "004" depuis "20260607-004-P005")
        order_id = plat.get("order_id", "")
        num_commande = order_id.split("-")[-1] if "-" in order_id else order_id
        id_label = QLabel(f"Commande n° {num_commande}")
        id_label.setStyleSheet(f"color: {_TEXT_ID}; font-size: 17px; font-weight: 700; border: none;")
        h.addWidget(id_label, 1)

        return row
