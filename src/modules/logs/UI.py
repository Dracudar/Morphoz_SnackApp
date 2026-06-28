#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI.py - Vue journal des événements applicatifs

Description:
    Interface Qt/PySide6 de consultation du journal applicatif (logs).
    Affiche les entrées des fichiers app_YYYYMMDD.log (format JSON Lines).
    La recherche libre reste accessible en permanence ; les filtres avancés
    (catégorie, événement, période) et les options de tri sont regroupés dans
    une fenêtre dédiée.
    Chaque entrée affiche : index, horodatage, catégorie, événement et détails.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.06.11

Date de modification:
    2026.06.21
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.utils.tactile import ScrollAreaTactile
from src.UI.utils.icones import icone
from src.backend.app_config import get_logs_folder_path
from src.backend.data_sources import signature_logs
from src.modules.logs.filtre_tri_dialog import FILTERS_DEFAULT, FiltreTriLogDialog


# ── Palette (identique à l'historique) ───────────────────────────────────────
_BG_MAIN     = "#2f3136"
_BG_CARD     = "#3a3d43"
_BG_DETAIL   = "#4a4e55"
_BORDER_CARD = "#7f7f7f"
_BORDER_DET  = "#60646c"
_TEXT_TITLE  = "#f5f5f5"
_TEXT_DIM    = "#a8acb3"
_TEXT_BODY   = "#d6d6d6"

# ── Couleurs des badges catégorie ─────────────────────────────────────────────
_CAT_COLORS: Dict[str, tuple] = {
    "commande":   ("#7a4a1a", "#c97a30"),
    "stock":      ("#1a3a5e", "#5a90c8"),
    "carte":      ("#3a1a5e", "#9b59b6"),
    "parametres": ("#1a4a2a", "#4caf50"),
    "systeme":    ("#3b3f46", "#a8acb3"),
    "erreur":     ("#5e1a1a", "#c0392b"),
}

# ── Libellés des catégories ───────────────────────────────────────────────────
_CAT_LABELS: Dict[str, str] = {
    "commande":   "Commande",
    "stock":      "Stock",
    "carte":      "Carte",
    "parametres": "Paramètres",
    "systeme":    "Système",
    "erreur":     "Erreur",
}


def _load_log_entries(logs_folder: Path) -> List[Dict[str, Any]]:
    """Lit tous les fichiers app_*.log du dossier et retourne la liste des entrées."""
    entries: List[Dict[str, Any]] = []
    if not logs_folder.exists():
        return entries
    for log_file in sorted(logs_folder.glob("app_*.log")):
        try:
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry.setdefault("_file", log_file.name)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        pass
        except OSError:
            pass
    return entries


def _parse_dt(date_text: str, time_text: str, default_time: str = "00:00") -> Optional[datetime]:
    date_text = date_text.strip()
    if not date_text:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            d = datetime.strptime(date_text, fmt)
            t_text = time_text.strip() or default_time
            try:
                t = datetime.strptime(t_text, "%H:%M")
                return d.replace(hour=t.hour, minute=t.minute)
            except ValueError:
                return d
        except ValueError:
            continue
    return None


def _entry_dt(entry: Dict[str, Any]) -> Optional[datetime]:
    ts = entry.get("timestamp", "")
    if not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


class LogsModule(QFrame):
    """Module de consultation du journal des événements applicatifs."""

    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logsModule")
        self._filters: Dict[str, Any] = dict(FILTERS_DEFAULT)
        self._filters["categories"] = set()
        self._filters["evenements"] = set()
        # État du rafraîchissement incrémental. Les entrées de journal sont immuables
        # (append-only) : une carte créée n'a jamais à être reconstruite.
        self._last_key = None                    # clé de court-circuit au dernier refresh
        self._cards: dict[tuple, QFrame] = {}    # carte par (fichier, index)
        self._displayed_order: list[tuple] = []  # ordre des cartes affichées
        self._empty_label: QLabel | None = None  # label "aucune entrée" éventuel
        self._build_ui()
        self._build_timer()
        self.refresh_entries()

    # ── Construction de l'interface ───────────────────────────────────────────

    def _build_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(8)

        # Titre
        title = QLabel("Journal des événements")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("sectionTitle")
        main_layout.addWidget(title)

        # Recherche + bouton filtres/tri
        search_row = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Rechercher dans le journal…")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.textChanged.connect(self.refresh_entries)

        self.filter_btn = QPushButton(" Filtres & Tri")
        self.filter_btn.setObjectName("filterOpenButton")
        self.filter_btn.setIcon(icone("filter.svg", 16))
        self.filter_btn.setIconSize(QSize(16, 16))
        self.filter_btn.clicked.connect(self._open_filter_dialog)

        search_row.addWidget(self.search_field, 1)
        search_row.addWidget(self.filter_btn)
        main_layout.addLayout(search_row)

        # Indicateur de filtres actifs
        self.filter_indicator = QLabel("")
        self.filter_indicator.setObjectName("filterIndicator")
        self.filter_indicator.setVisible(False)
        main_layout.addWidget(self.filter_indicator)

        # Zone scrollable
        self.scroll_area = ScrollAreaTactile(_BG_MAIN)
        main_layout.addWidget(self.scroll_area, 1)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.list_container)

        # Barre de bas : retour + compteur
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 4, 0, 0)

        self.back_button = QPushButton("  Retour")
        self.back_button.setObjectName("backButton")
        self.back_button.setIcon(icone("return.svg", 18))
        self.back_button.setIconSize(QSize(18, 18))
        self.back_button.clicked.connect(self.go_back.emit)

        self.summary_label = QLabel("Entrées : 0")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setObjectName("summaryLabel")

        bottom_bar.addWidget(self.back_button)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.summary_label)
        bottom_bar.addStretch()
        main_layout.addLayout(bottom_bar)

        self.setStyleSheet(
            f"""
            QFrame#logsModule {{
                background-color: {_BG_MAIN};
                border: 1px solid {_BORDER_CARD};
            }}
            QLabel#sectionTitle {{
                color: {_TEXT_TITLE};
                font-size: 22px;
                font-weight: 700;
                padding: 4px;
            }}
            QLabel#filterIndicator {{
                color: #c97a30;
                font-size: 12px;
                padding: 2px 4px;
            }}
            QLabel#summaryLabel {{
                color: {_TEXT_DIM};
                font-size: 13px;
                font-weight: 600;
            }}
            QLineEdit {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 6px;
                padding: 6px 8px;
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
            QPushButton#backButton:hover {{ background-color: #626978; }}
            QPushButton#filterOpenButton {{
                background-color: #4f545e;
                border: 1px solid #7d8390;
                border-radius: 7px;
                color: {_TEXT_TITLE};
                font-size: 14px;
                font-weight: 700;
                padding: 6px 12px;
            }}
            QPushButton#filterOpenButton:hover {{ background-color: #626978; }}
            """
        )

    def _build_timer(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(10_000)
        self.refresh_timer.timeout.connect(self.refresh_entries)
        self.refresh_timer.start()

    # ── Dialog filtres/tri ────────────────────────────────────────────────────

    def _open_filter_dialog(self):
        dialog = FiltreTriLogDialog(parent=self, current_filters=self._filters)
        if dialog.exec():
            self._filters = dialog.get_filters()
            self._update_filter_indicator()
            self.refresh_entries()

    def _count_active_filters(self) -> int:
        f = self._filters
        n = 0
        if f.get("categories"):
            n += 1
        if f.get("evenements"):
            n += 1
        if f.get("date_from") or f.get("date_to"):
            n += 1
        tri = f.get("tri", "timestamp_desc")
        if tri and tri != "timestamp_desc":
            n += 1
        return n

    def _update_filter_indicator(self):
        n = self._count_active_filters()
        if n > 0:
            self.filter_btn.setText(f" Filtres & Tri · {n} actif{'s' if n > 1 else ''}")
            self.filter_btn.setStyleSheet(
                """
                QPushButton#filterOpenButton {
                    background-color: #4a3a1a;
                    border: 1px solid #c97a30;
                    border-radius: 7px;
                    color: #c97a30;
                    font-size: 14px;
                    font-weight: 700;
                    padding: 6px 12px;
                }
                QPushButton#filterOpenButton:hover { background-color: #5a4a2a; }
                """
            )
            self.filter_indicator.setText(self._describe_active_filters())
            self.filter_indicator.setVisible(True)
        else:
            self.filter_btn.setText(" Filtres & Tri")
            self.filter_btn.setStyleSheet("")
            self.filter_indicator.setVisible(False)

    def _describe_active_filters(self) -> str:
        f = self._filters
        parts = []
        cats: Set[str] = set(f.get("categories") or set())
        if cats:
            parts.append(", ".join(_CAT_LABELS.get(c, c) for c in sorted(cats)))
        evts: Set[str] = set(f.get("evenements") or set())
        if evts:
            parts.append(", ".join(sorted(evts)))
        date_from, time_from = f.get("date_from", ""), f.get("time_from", "")
        date_to, time_to = f.get("date_to", ""), f.get("time_to", "")
        if date_from or date_to:
            from_str = f"{date_from} {time_from}".strip() if date_from else "…"
            to_str = f"{date_to} {time_to}".strip() if date_to else "…"
            parts.append(f"{from_str} → {to_str}")
        tri = f.get("tri", "timestamp_desc")
        if tri and tri != "timestamp_desc":
            from src.modules.logs.filtre_tri_dialog import TRI_OPTIONS
            label = next((lbl for lbl, k in TRI_OPTIONS if k == tri), tri)
            parts.append(f"Tri : {label}")
        return "  ·  ".join(parts)

    # ── Filtrage et tri ───────────────────────────────────────────────────────

    def _apply_filters(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        f = self._filters
        cats: Set[str] = set(f.get("categories") or set())
        evts: Set[str] = set(f.get("evenements") or set())

        if cats:
            entries = [e for e in entries if e.get("categorie", "").lower() in cats]
        if evts:
            entries = [e for e in entries if e.get("evenement", "") in evts]

        dt_from = _parse_dt(f.get("date_from", ""), f.get("time_from", ""), "00:00")
        dt_to   = _parse_dt(f.get("date_to", ""),   f.get("time_to", ""),   "23:59")
        if dt_from or dt_to:
            filtered = []
            for e in entries:
                dt = _entry_dt(e)
                if dt is None:
                    continue
                if dt_from and dt < dt_from:
                    continue
                if dt_to and dt > dt_to:
                    continue
                filtered.append(e)
            entries = filtered

        query = self.search_field.text().strip().lower()
        if query:
            entries = [e for e in entries if self._matches_search(e, query)]

        entries = self._sort_entries(entries, f.get("tri", "timestamp_desc"))
        return entries

    def _matches_search(self, entry: Dict[str, Any], query: str) -> bool:
        haystack = [
            str(entry.get("index", "")),
            str(entry.get("timestamp", "")),
            str(entry.get("categorie", "")),
            str(entry.get("evenement", "")),
            json.dumps(entry.get("details", {}), ensure_ascii=False),
        ]
        return any(query in v.lower() for v in haystack if v)

    def _sort_entries(self, entries: List[Dict[str, Any]], tri: str) -> List[Dict[str, Any]]:
        if tri == "timestamp_asc":
            return sorted(entries, key=lambda e: e.get("timestamp", ""))
        if tri == "timestamp_desc":
            return sorted(entries, key=lambda e: e.get("timestamp", ""), reverse=True)
        if tri == "index_asc":
            return sorted(entries, key=lambda e: (e.get("_file", ""), e.get("index", 0)))
        if tri == "index_desc":
            return sorted(entries, key=lambda e: (e.get("_file", ""), e.get("index", 0)), reverse=True)
        if tri == "categorie_asc":
            return sorted(entries, key=lambda e: (e.get("categorie", ""), e.get("timestamp", "")))
        if tri == "evenement_asc":
            return sorted(entries, key=lambda e: (e.get("evenement", ""), e.get("timestamp", "")))
        return entries

    # ── Rafraîchissement ──────────────────────────────────────────────────────

    def clear_cards(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._cards.clear()
        self._displayed_order.clear()
        self._empty_label = None

    def _filters_snapshot(self) -> tuple:
        """Capture hashable des filtres, du tri et de la recherche, pour le court-circuit."""
        f = self._filters
        return (
            frozenset(f.get("categories") or set()),
            frozenset(f.get("evenements") or set()),
            f.get("date_from", ""), f.get("time_from", ""),
            f.get("date_to", ""), f.get("time_to", ""),
            f.get("tri", "timestamp_desc"),
            self.search_field.text().strip().lower(),
        )

    def refresh_entries(self):
        # Couche 2 — court-circuit : clé combinant l'état du dossier de logs, les
        # filtres, le tri et la recherche.
        cle = (signature_logs(), self._filters_snapshot())
        if cle == self._last_key:
            return
        self._last_key = cle

        entries = _load_log_entries(get_logs_folder_path())
        entries = self._apply_filters(entries)

        self.summary_label.setText(f"Entrées : {len(entries)}")

        # Label "aucune entrée" : état exclusif des cartes.
        if self._empty_label is not None:
            self.list_layout.removeWidget(self._empty_label)
            self._empty_label.deleteLater()
            self._empty_label = None

        if not entries:
            self.clear_cards()
            self._empty_label = QLabel("Aucune entrée trouvée.")
            self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_label.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 14px; padding: 20px;")
            self.list_layout.insertWidget(0, self._empty_label)
            return

        # Couche 3 — diff : entrées immuables, on ajoute/retire/réordonne seulement.
        nouvel_ordre = [(e.get("_file", ""), e.get("index", 0)) for e in entries]
        nouvel_ensemble = set(nouvel_ordre)

        for cle_carte in list(self._cards.keys()):
            if cle_carte not in nouvel_ensemble:
                ancienne = self._cards.pop(cle_carte)
                self.list_layout.removeWidget(ancienne)
                ancienne.deleteLater()

        for entry, cle_carte in zip(entries, nouvel_ordre):
            if cle_carte not in self._cards:
                card = self._build_entry_card(entry)
                self._cards[cle_carte] = card
                self.list_layout.insertWidget(self.list_layout.count() - 1, card)

        if nouvel_ordre != self._displayed_order:
            for cle_carte in nouvel_ordre:
                self.list_layout.removeWidget(self._cards[cle_carte])
            for position, cle_carte in enumerate(nouvel_ordre):
                self.list_layout.insertWidget(position, self._cards[cle_carte])
            self._displayed_order = nouvel_ordre

    # ── Construction des cartes ───────────────────────────────────────────────

    def _build_entry_card(self, entry: Dict[str, Any]) -> QFrame:
        card = QFrame()
        card.setObjectName("logCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(4)

        # Ligne principale : index · timestamp · badge catégorie · événement
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        index_lbl = QLabel(f"#{entry.get('index', '?')}")
        index_lbl.setStyleSheet(
            f"color: {_TEXT_DIM}; font-size: 12px; font-weight: 600; min-width: 36px;"
        )
        header_row.addWidget(index_lbl)

        ts = entry.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                ts_display = dt.strftime("%d/%m/%Y %H:%M:%S")
            except ValueError:
                ts_display = ts
        else:
            ts_display = "-"
        ts_lbl = QLabel(ts_display)
        ts_lbl.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 12px;")
        header_row.addWidget(ts_lbl)

        header_row.addWidget(self._build_cat_badge(entry.get("categorie", "")))

        evt_lbl = QLabel(entry.get("evenement", ""))
        evt_lbl.setStyleSheet(f"color: {_TEXT_TITLE}; font-size: 13px; font-weight: 700;")
        header_row.addWidget(evt_lbl, 1)

        card_layout.addLayout(header_row)

        # Détails (si non vides)
        details = entry.get("details") or {}
        if details:
            card_layout.addWidget(self._build_details_panel(details))

        card.setStyleSheet(
            f"""
            QFrame#logCard {{
                background-color: {_BG_CARD};
                border: 1px solid {_BORDER_CARD};
                border-radius: 6px;
            }}
            """
        )
        return card

    def _build_cat_badge(self, categorie: str) -> QLabel:
        key = categorie.lower()
        bg, fg = _CAT_COLORS.get(key, ("#3a3d43", "#7a7f87"))
        label_text = _CAT_LABELS.get(key, categorie or "?")
        badge = QLabel(label_text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {fg};
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
                padding: 1px 8px;
            }}
            """
        )
        return badge

    def _build_details_panel(self, details: Dict[str, Any]) -> QFrame:
        panel = QFrame()
        panel.setObjectName("detailPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)

        items = list(details.items())
        for i, (key, value) in enumerate(items):
            if i > 0:
                sep = QLabel("·")
                sep.setStyleSheet(f"color: {_BORDER_DET}; font-size: 12px; padding: 0 8px;")
                layout.addWidget(sep)
            key_w = QLabel(f"{key} :")
            key_w.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 11px;")
            val_text = str(value) if not isinstance(value, (dict, list)) else json.dumps(value, ensure_ascii=False)
            val_w = QLabel(val_text)
            val_w.setStyleSheet(
                f"color: {_TEXT_BODY}; font-size: 11px; font-weight: 600; margin-left: 4px;"
            )
            val_w.setWordWrap(True)
            layout.addWidget(key_w)
            layout.addWidget(val_w)

        layout.addStretch()
        panel.setStyleSheet(
            f"""
            QFrame#detailPanel {{
                background-color: {_BG_DETAIL};
                border: 1px solid {_BORDER_DET};
                border-radius: 4px;
            }}
            """
        )
        return panel
