#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filtre_tri_dialog.py - Fenêtre de paramétrage des filtres et du tri du journal

Description:
    QDialog regroupant tous les paramètres de filtrage et de tri de la vue journal :
    catégorie, événement, période (date + heure) et ordre de tri.
    Trois boutons en pied de fenêtre : appliquer, annuler, remise à zéro.

Auteur :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.11
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# ── Couleurs (identiques à filtre_dialog de l'historique) ────────────────────
_BG_DIALOG  = "#36393f"
_BG_SECTION = "#2f3136"
_BORDER     = "#60646c"
_TEXT_TITLE = "#f5f5f5"
_TEXT_LABEL = "#a8acb3"

# ── Catégories disponibles ────────────────────────────────────────────────────
CATEGORIES: List[tuple] = [
    ("Commande",   "commande"),
    ("Stock",      "stock"),
    ("Carte",      "carte"),
    ("Paramètres", "parametres"),
    ("Système",    "systeme"),
    ("Erreur",     "erreur"),
]

# ── Événements par catégorie ──────────────────────────────────────────────────
EVENEMENTS_PAR_CATEGORIE: Dict[str, List[tuple]] = {
    "commande": [
        ("Ajout plat",        "AJOUT_PLAT"),
        ("Annul. plat",       "ANNULATION_PLAT"),
        ("Annul. commande",   "ANNULATION_COMMANDE"),
        ("Validation",        "VALIDATION_COMMANDE"),
        ("Plat prêt",         "PLAT_PRET"),
        ("Plat livré",        "PLAT_LIVRE"),
        ("Plat non livré",    "PLAT_NON_LIVRE"),
        ("Transfert prêt",    "TRANSFERT_PRET"),
        ("Cmd terminée",      "COMMANDE_TERMINEE"),
        ("Impression ticket", "IMPRESSION_TICKET"),
    ],
    "stock": [
        ("Modif. manuelle",   "MODIFICATION_STOCK_MANUELLE"),
        ("Modif. cache",      "MODIFICATION_CACHE_STOCK"),
        ("Persistance",       "PERSISTANCE_STOCK"),
    ],
    "carte": [
        ("Modif. manuelle",   "MODIFICATION_CARTE_MANUELLE"),
    ],
    "parametres": [
        ("Imprimante",        "MODIFICATION_PARAMETRES_IMPRIMANTE"),
        ("Options impression","MODIFICATION_OPTIONS_IMPRESSION"),
        ("Dossier données",   "MODIFICATION_DOSSIER_DONNEES"),
    ],
    "systeme": [
        ("Fichier corrompu",  "FICHIER_CORROMPU"),
        ("Affichage ext.",    "AFFICHAGE_EXTERIEUR"),
        ("Création fichier",  "CREATION_FICHIER"),
        ("Création dossier",  "CREATION_DOSSIER"),
        ("Démarrage",         "DEMARRAGE_APP"),
        ("Arrêt",             "ARRET_APP"),
    ],
    "erreur": [
        ("Erreur",            "ERREUR"),
    ],
}

# ── Options de tri ────────────────────────────────────────────────────────────
TRI_OPTIONS: List[tuple] = [
    ("Plus récent",  "timestamp_desc"),
    ("Plus ancien",  "timestamp_asc"),
    ("Index ↓",      "index_desc"),
    ("Index ↑",      "index_asc"),
    ("Catégorie",    "categorie_asc"),
    ("Événement",    "evenement_asc"),
]

# Valeurs par défaut
FILTERS_DEFAULT: Dict[str, Any] = {
    "categories":  set(),
    "evenements":  set(),
    "date_from":   "",
    "time_from":   "",
    "date_to":     "",
    "time_to":     "",
    "tri":         "timestamp_desc",
}


class FiltreTriLogDialog(QDialog):
    """Fenêtre modale de paramétrage des filtres et du tri du journal."""

    def __init__(
        self,
        parent=None,
        current_filters: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Filtres & Tri — Journal")
        self.setModal(True)
        self.setMinimumWidth(500)

        self._initial_filters: Dict[str, Any] = dict(current_filters or FILTERS_DEFAULT)
        self._cat_btns: Dict[str, QPushButton] = {}
        self._evt_btns: Dict[str, QPushButton] = {}
        self._tri_btns: Dict[str, QPushButton] = {}
        self._evt_section_layout: Optional[QVBoxLayout] = None

        self._build_ui()
        self._load_filters(self._initial_filters)

    # ── Construction ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        root.addWidget(self._section_categories())
        self._evt_section_widget = self._section_evenements()
        root.addWidget(self._evt_section_widget)
        root.addWidget(self._section_periode())
        root.addWidget(self._section_tri())
        root.addStretch()
        root.addWidget(self._build_footer())

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {_BG_DIALOG};
            }}
            QFrame#section {{
                background-color: {_BG_SECTION};
                border: 1px solid {_BORDER};
                border-radius: 6px;
            }}
            QLabel#sectionTitle {{
                color: {_TEXT_TITLE};
                font-size: 13px;
                font-weight: 700;
            }}
            QLabel#fieldLabel {{
                color: {_TEXT_LABEL};
                font-size: 12px;
            }}
            QLineEdit {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 5px;
                padding: 5px 8px;
            }}
            QPushButton#filterBtn {{
                background-color: #3a3d43;
                border: 1px solid {_BORDER};
                border-radius: 12px;
                color: {_TEXT_LABEL};
                font-size: 12px;
                font-weight: 600;
                padding: 3px 14px;
                min-height: 26px;
            }}
            QPushButton#filterBtn:checked {{
                background-color: #4f545e;
                border: 1px solid #a8acb3;
                color: {_TEXT_TITLE};
            }}
            QPushButton#filterBtn:hover:!checked {{
                background-color: #4a4e55;
            }}
            QPushButton#triBtn {{
                background-color: #3a3d43;
                border: 1px solid {_BORDER};
                border-radius: 12px;
                color: {_TEXT_LABEL};
                font-size: 12px;
                font-weight: 600;
                padding: 3px 14px;
                min-height: 26px;
            }}
            QPushButton#triBtn:checked {{
                background-color: #1a3a5e;
                border: 1px solid #5a90c8;
                color: {_TEXT_TITLE};
            }}
            QPushButton#triBtn:hover:!checked {{
                background-color: #4a4e55;
            }}
            QPushButton#applyBtn {{
                background-color: #2d6a4f;
                border: 1px solid #40916c;
                border-radius: 7px;
                color: {_TEXT_TITLE};
                font-size: 14px;
                font-weight: 700;
                min-height: 36px;
                padding: 6px 16px;
            }}
            QPushButton#applyBtn:hover {{ background-color: #40916c; }}
            QPushButton#cancelBtn {{
                background-color: #4f545e;
                border: 1px solid #7d8390;
                border-radius: 7px;
                color: {_TEXT_TITLE};
                font-size: 14px;
                font-weight: 700;
                min-height: 36px;
                padding: 6px 16px;
            }}
            QPushButton#cancelBtn:hover {{ background-color: #626978; }}
            QPushButton#resetBtn {{
                background-color: #5e1a1a;
                border: 1px solid #c0392b;
                border-radius: 7px;
                color: {_TEXT_TITLE};
                font-size: 14px;
                font-weight: 700;
                min-height: 36px;
                padding: 6px 16px;
            }}
            QPushButton#resetBtn:hover {{ background-color: #c0392b; }}
            """
        )

    def _make_section(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("section")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        lbl = QLabel(title)
        lbl.setObjectName("sectionTitle")
        layout.addWidget(lbl)
        return frame, layout

    def _section_categories(self) -> QFrame:
        frame, layout = self._make_section("Catégorie")
        row = QHBoxLayout()
        row.setSpacing(6)
        for label, key in CATEGORIES:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("filterBtn")
            btn.clicked.connect(lambda _, k=key: self._on_categorie_toggle(k))
            self._cat_btns[key] = btn
            row.addWidget(btn)
        row.addStretch()
        layout.addLayout(row)
        return frame

    def _section_evenements(self) -> QFrame:
        frame, layout = self._make_section("Événement")
        self._evt_section_layout = layout
        self._rebuild_evenements_row(set())
        return frame

    def _rebuild_evenements_row(self, active_categories: Set[str]):
        """Reconstruit la liste des boutons événement selon les catégories actives."""
        if self._evt_section_layout is None:
            return

        # Supprimer les lignes d'événements existantes (garder le titre en index 0)
        while self._evt_section_layout.count() > 1:
            item = self._evt_section_layout.takeAt(1)
            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

        self._evt_btns.clear()

        # Déterminer quels événements afficher
        if active_categories:
            evts = []
            for cat in active_categories:
                evts.extend(EVENEMENTS_PAR_CATEGORIE.get(cat, []))
        else:
            evts = []
            for lst in EVENEMENTS_PAR_CATEGORIE.values():
                evts.extend(lst)

        if not evts:
            return

        # Découper en rangées de max 4 boutons
        chunk_size = 4
        for i in range(0, len(evts), chunk_size):
            row = QHBoxLayout()
            row.setSpacing(6)
            for label, key in evts[i:i + chunk_size]:
                btn = QPushButton(label)
                btn.setCheckable(True)
                btn.setObjectName("filterBtn")
                self._evt_btns[key] = btn
                row.addWidget(btn)
            row.addStretch()
            self._evt_section_layout.addLayout(row)

    def _on_categorie_toggle(self, key: str):
        active = {k for k, b in self._cat_btns.items() if b.isChecked()}
        prev_checked = {k for k in self._evt_btns if self._evt_btns[k].isChecked()}
        self._rebuild_evenements_row(active)
        # Restaurer les états cochés compatibles
        for k, btn in self._evt_btns.items():
            if k in prev_checked:
                btn.setChecked(True)

    def _section_periode(self) -> QFrame:
        frame, layout = self._make_section("Période")

        du_row = QHBoxLayout()
        du_row.setSpacing(6)
        du_lbl = QLabel("Du")
        du_lbl.setObjectName("fieldLabel")
        du_lbl.setFixedWidth(22)
        du_row.addWidget(du_lbl)
        self.date_from = QLineEdit()
        self.date_from.setPlaceholderText("JJ/MM/AAAA")
        self.date_from.setMaximumWidth(115)
        du_row.addWidget(self.date_from)
        self.time_from = QLineEdit()
        self.time_from.setPlaceholderText("HH:MM")
        self.time_from.setMaximumWidth(68)
        du_row.addWidget(self.time_from)
        du_row.addStretch()
        layout.addLayout(du_row)

        au_row = QHBoxLayout()
        au_row.setSpacing(6)
        au_lbl = QLabel("Au")
        au_lbl.setObjectName("fieldLabel")
        au_lbl.setFixedWidth(22)
        au_row.addWidget(au_lbl)
        self.date_to = QLineEdit()
        self.date_to.setPlaceholderText("JJ/MM/AAAA")
        self.date_to.setMaximumWidth(115)
        au_row.addWidget(self.date_to)
        self.time_to = QLineEdit()
        self.time_to.setPlaceholderText("HH:MM")
        self.time_to.setMaximumWidth(68)
        au_row.addWidget(self.time_to)
        au_row.addStretch()
        layout.addLayout(au_row)

        return frame

    def _section_tri(self) -> QFrame:
        frame, layout = self._make_section("Tri")
        row = QHBoxLayout()
        row.setSpacing(6)
        for label, key in TRI_OPTIONS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("triBtn")
            btn.clicked.connect(lambda _, k=key: self._on_tri_click(k))
            self._tri_btns[key] = btn
            row.addWidget(btn)
        row.addStretch()
        layout.addLayout(row)
        return frame

    def _on_tri_click(self, key: str):
        for k, btn in self._tri_btns.items():
            btn.setChecked(k == key)

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        apply_btn = QPushButton("Fermer et appliquer")
        apply_btn.setObjectName("applyBtn")
        apply_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)

        reset_btn = QPushButton("Raz")
        reset_btn.setObjectName("resetBtn")
        reset_btn.clicked.connect(self._reset_and_accept)

        layout.addWidget(apply_btn, 1)
        layout.addWidget(cancel_btn)
        layout.addWidget(reset_btn)
        return footer

    # ── Logique interne ───────────────────────────────────────────────────────

    def _load_filters(self, filters: Dict[str, Any]):
        active_cats: Set[str] = set(filters.get("categories") or set())
        for k, btn in self._cat_btns.items():
            btn.setChecked(k in active_cats)

        self._rebuild_evenements_row(active_cats)
        active_evts: Set[str] = set(filters.get("evenements") or set())
        for k, btn in self._evt_btns.items():
            btn.setChecked(k in active_evts)

        self.date_from.setText(filters.get("date_from", ""))
        self.time_from.setText(filters.get("time_from", ""))
        self.date_to.setText(filters.get("date_to", ""))
        self.time_to.setText(filters.get("time_to", ""))

        tri = filters.get("tri", "timestamp_desc")
        for k, btn in self._tri_btns.items():
            btn.setChecked(k == tri)

    def _reset_and_accept(self):
        self._load_filters(dict(FILTERS_DEFAULT))
        self.accept()

    # ── API publique ──────────────────────────────────────────────────────────

    def get_filters(self) -> Dict[str, Any]:
        active_cats: Set[str] = {k for k, b in self._cat_btns.items() if b.isChecked()}
        active_evts: Set[str] = {k for k, b in self._evt_btns.items() if b.isChecked()}
        tri = next((k for k, b in self._tri_btns.items() if b.isChecked()), "timestamp_desc")
        return {
            "categories": active_cats,
            "evenements": active_evts,
            "date_from":  self.date_from.text().strip(),
            "time_from":  self.time_from.text().strip(),
            "date_to":    self.date_to.text().strip(),
            "time_to":    self.time_to.text().strip(),
            "tri":        tri,
        }
