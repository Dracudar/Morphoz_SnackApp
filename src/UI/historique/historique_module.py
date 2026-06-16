#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
historique_module.py

Description:
    Interface Qt/PySide6 de consultation de l'historique des commandes.
    Affiche toutes les commandes (en cours, terminées, annulées) sauf celles
    en cours de saisie et les fichiers corrompus.
    La recherche libre reste accessible en permanence ; les filtres avancés
    (statut, période, type de plat) sont regroupés dans une fenêtre dédiée.
    Pour les commandes "validées", des boutons permettent de changer le statut
    des plats "en préparation" ou "prêts" (→ Prêt, → Livré, annuler) et de
    réimprimer les tickets récap (par commande) ou cuisine (par plat).
    Un bouton global en bas à droite réimprime tous les tickets cuisine actifs.

    La construction des cartes (tableau_commandes.py) et les actions de
    réimpression/statut (detail_commande.py) sont mélangées (mixins) dans
    CommandesHistoriqueModule, qui assure l'assemblage de l'interface, le
    filtrage et le rafraîchissement périodique.

Author :
    Dracudar

Version:
    3.7

Date de création :
    2026.05.26

Date de modification:
    2026.06.16
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtGui import QIcon
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
from src.backend.config.impression import get_print_options
from src.backend.data.commandes import get_all_history_orders
from src.UI.historique.detail_commande import _DetailCommandeMixin
from src.UI.historique.filtre_dialog import FiltreHistoriqueDialog
from src.UI.historique.tableau_commandes import (
    _BG_MAIN,
    _BORDER_CARD,
    _STATUTS_PLAT,
    _TableauCommandesMixin,
    _TEXT_CARD_CNT,
    _TEXT_TITLE,
)


# ── Labels statut pour l'indicateur de filtres actifs ────────────────────────
_STATUT_LABELS = {"validée": "En cours", "terminée": "Terminée", "annulée": "Annulée"}

# ── État de filtres par défaut (aucun filtre actif) ──────────────────────────
_FILTERS_DEFAULT: Dict[str, Any] = {
    "status":        None,
    "date_from":     "",
    "time_from":     "",
    "date_to":       "",
    "time_to":       "",
    "plat_types":    set(),
    "plat_statuses": set(),
    "priority_only": False,
}


class CommandesHistoriqueModule(QFrame, _TableauCommandesMixin, _DetailCommandeMixin):
    """Module de consultation de l'historique de toutes les commandes."""

    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("historiqueModule")
        self._expanded_orders: set[str] = set()
        self._filters: Dict[str, Any] = dict(_FILTERS_DEFAULT)
        self._filters["plat_types"] = set()
        self._build_ui()
        self._build_timer()
        self.refresh_orders()

    # ── Construction de l'interface ─────────────────────────────────────────

    def _build_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(8)

        # Titre
        title = QLabel("Historique des commandes")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("sectionTitle")
        main_layout.addWidget(title)

        # Ligne : recherche + bouton filtres
        search_row = QHBoxLayout()
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Rechercher par ID, plat ou statut…")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.textChanged.connect(self.refresh_orders)

        self.filter_btn = QPushButton(" Filtres")
        self.filter_btn.setObjectName("filterOpenButton")
        self.filter_btn.setIcon(QIcon("assets/icons/filter.svg"))
        self.filter_btn.setIconSize(QSize(16, 16))
        self.filter_btn.clicked.connect(self._open_filter_dialog)

        search_row.addWidget(self.search_field, 1)
        search_row.addWidget(self.filter_btn)
        main_layout.addLayout(search_row)

        # Indicateur de filtres actifs (masqué par défaut)
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
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.list_container)

        # Barre de bas : bouton retour + compteur centré + impression cuisine active
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 4, 0, 0)

        self.back_button = QPushButton("  Retour")
        self.back_button.setObjectName("backButton")
        self.back_button.setIcon(QIcon("assets/icons/return.svg"))
        self.back_button.setIconSize(QSize(18, 18))
        self.back_button.clicked.connect(self.go_back.emit)

        self.summary_label = QLabel("Commandes : 0  ·  Plats : 0")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.summary_label.setObjectName("summaryLabel")

        self.print_all_btn = QPushButton("  Tickets cuisine (en cours)")
        self.print_all_btn.setObjectName("printAllButton")
        self.print_all_btn.setIcon(QIcon("assets/icons/print.svg"))
        self.print_all_btn.setIconSize(QSize(16, 16))
        self.print_all_btn.setToolTip("Imprimer les tickets cuisine de tous les plats en préparation ou prêts")
        self.print_all_btn.clicked.connect(self._on_print_all_active)

        bottom_bar.addWidget(self.back_button)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.summary_label)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.print_all_btn)
        main_layout.addLayout(bottom_bar)

        self.setStyleSheet(
            f"""
            QFrame#historiqueModule {{
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
                color: {_TEXT_CARD_CNT};
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
            QPushButton#backButton:hover {{
                background-color: #626978;
            }}
            QPushButton#filterOpenButton {{
                background-color: #4f545e;
                border: 1px solid #7d8390;
                border-radius: 7px;
                color: {_TEXT_TITLE};
                font-size: 14px;
                font-weight: 700;
                padding: 6px 12px;
            }}
            QPushButton#filterOpenButton:hover {{
                background-color: #626978;
            }}
            QPushButton#printAllButton {{
                background-color: #4f545e;
                border: 1px solid #7d8390;
                border-radius: 7px;
                color: {_TEXT_TITLE};
                font-size: 14px;
                font-weight: 700;
                min-height: 38px;
                padding: 6px 12px;
            }}
            QPushButton#printAllButton:hover:enabled {{
                background-color: #626978;
            }}
            QPushButton#printAllButton:disabled {{
                background-color: #3b3f46;
                border: 1px solid #4a4e55;
                color: #595d64;
            }}
            """
        )

    def _build_timer(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(self.refresh_orders)
        self.refresh_timer.start()

    # ── Gestion du dialog filtres ───────────────────────────────────────────

    def _open_filter_dialog(self):
        """Ouvre la fenêtre de filtres ; applique les changements si acceptés."""
        plat_types = self._get_available_plat_types()
        dialog = FiltreHistoriqueDialog(
            parent=self,
            current_filters=self._filters,
            available_plat_types=plat_types,
        )
        if dialog.exec():
            self._filters = dialog.get_filters()
            self._update_filter_indicator()
            self.refresh_orders()

    def _get_available_plat_types(self) -> List[str]:
        """Collecte les types de plat distincts présents dans l'historique."""
        orders = get_all_history_orders()
        types: Set[str] = set()
        for order in orders:
            for item in order.get("items", []):
                plat = item.get("plat", "").strip()
                if plat:
                    types.add(plat)
        return sorted(types)

    def _count_active_filters(self) -> int:
        """Retourne le nombre de catégories de filtres actuellement actives."""
        f = self._filters
        n = 0
        if f.get("status") is not None:
            n += 1
        if f.get("priority_only"):
            n += 1
        if f.get("date_from") or f.get("date_to"):
            n += 1
        if f.get("plat_types"):
            n += 1
        if f.get("plat_statuses"):
            n += 1
        return n

    def _update_filter_indicator(self):
        """Met à jour le bouton filtres et l'indicateur textuel selon l'état actif."""
        n = self._count_active_filters()
        if n > 0:
            self.filter_btn.setText(f" Filtres · {n} actif{'s' if n > 1 else ''}")
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
            self.filter_btn.setText(" Filtres")
            self.filter_btn.setStyleSheet("")
            self.filter_indicator.setVisible(False)

    def _describe_active_filters(self) -> str:
        """Construit un résumé textuel des filtres actifs pour l'indicateur."""
        f = self._filters
        parts = []
        if f.get("status"):
            parts.append(_STATUT_LABELS.get(f["status"], f["status"]))
        if f.get("priority_only"):
            parts.append("Prioritaire")
        date_from, time_from = f.get("date_from", ""), f.get("time_from", "")
        date_to, time_to = f.get("date_to", ""), f.get("time_to", "")
        if date_from or date_to:
            from_str = f"{date_from} {time_from}".strip() if date_from else "…"
            to_str = f"{date_to} {time_to}".strip() if date_to else "…"
            parts.append(f"{from_str} → {to_str}")
        plat_types = f.get("plat_types") or set()
        if plat_types:
            parts.append(", ".join(sorted(plat_types)))
        plat_statuses = f.get("plat_statuses") or set()
        if plat_statuses:
            labels = [_STATUTS_PLAT.get(s, (None, None, s))[2] for s in sorted(plat_statuses)]
            parts.append(", ".join(labels))
        return "  ·  ".join(parts)

    # ── Logique de filtrage ─────────────────────────────────────────────────

    def _parse_filter_datetime(
        self, date_text: str, time_text: str, default_time: str = "00:00"
    ) -> Optional[datetime]:
        """Construit un datetime depuis les champs date + heure du filtre.

        Utilise default_time si l'heure est absente ("00:00" côté début, "23:59" côté fin).
        """
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

    def _get_order_datetime(self, order: Dict[str, Any]) -> Optional[datetime]:
        """Retourne le datetime complet de création de la commande (date + heure)."""
        created = order.get("created_at", ["", ""])
        if not isinstance(created, list) or not created:
            return None
        date_str = str(created[0]).strip()
        time_str = str(created[1]).strip() if len(created) >= 2 else ""
        if not date_str:
            return None
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                d = datetime.strptime(date_str, fmt)
                if time_str:
                    try:
                        t = datetime.strptime(time_str, "%H:%M")
                        return d.replace(hour=t.hour, minute=t.minute)
                    except ValueError:
                        pass
                return d
            except ValueError:
                continue
        return None

    def _matches_search(self, order: Dict[str, Any], query: str) -> bool:
        haystack = [
            str(order.get("id", "")),
            str(order.get("status", "")),
            str(order.get("amount", "")),
        ]
        for item in order.get("items", []):
            haystack.extend([
                str(item.get("id", "")),
                str(item.get("nom", "")),
                str(item.get("plat", "")),
                str(item.get("status", "")),
            ])
        return any(query in value.lower() for value in haystack if value)

    # ── Données et affichage ────────────────────────────────────────────────

    def clear_cards(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh_orders(self):
        impression_active = get_print_options()["impression_active"]
        self.print_all_btn.setEnabled(impression_active)
        self.print_all_btn.setToolTip(
            "Imprimer les tickets cuisine de tous les plats en préparation ou prêts"
            if impression_active else "Impression désactivée"
        )

        orders = get_all_history_orders()
        f = self._filters

        # Filtre statut commande
        if f.get("status") is not None:
            orders = [o for o in orders if o.get("status", "").lower() == f["status"]]

        # Filtre commandes prioritaires
        if f.get("priority_only"):
            orders = [o for o in orders if o.get("priority", False)]

        # Filtre période
        dt_from = self._parse_filter_datetime(f.get("date_from", ""), f.get("time_from", ""), "00:00")
        dt_to   = self._parse_filter_datetime(f.get("date_to", ""),   f.get("time_to", ""),   "23:59")
        if dt_from or dt_to:
            filtered = []
            for o in orders:
                dt = self._get_order_datetime(o)
                if dt is None:
                    continue
                if dt_from and dt < dt_from:
                    continue
                if dt_to and dt > dt_to:
                    continue
                filtered.append(o)
            orders = filtered

        # Filtres plat (type et statut) : seuls les plats correspondants sont affichés
        active_types: Set[str] = set(f.get("plat_types") or set())
        active_plat_statuses: Set[str] = set(f.get("plat_statuses") or set())
        if active_types or active_plat_statuses:
            filtered_orders = []
            for o in orders:
                visible_items = [
                    item for item in o.get("items", [])
                    if (not active_types or item.get("plat", "").strip() in active_types)
                    and (not active_plat_statuses or item.get("status", "").lower() in active_plat_statuses)
                ]
                if visible_items:
                    order_copy = dict(o)
                    order_copy["items"] = visible_items
                    filtered_orders.append(order_copy)
            orders = filtered_orders

        # Filtre recherche libre
        query = self.search_field.text().strip().lower()
        if query:
            orders = [o for o in orders if self._matches_search(o, query)]

        self.clear_cards()
        total_plats = sum(len(o.get("items", [])) for o in orders)
        self.summary_label.setText(f"Commandes : {len(orders)}  ·  Plats : {total_plats}")

        if not orders:
            empty = QLabel("Aucune commande trouvée.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {_TEXT_CARD_CNT}; font-size: 14px; padding: 20px;")
            self.list_layout.insertWidget(0, empty)
            return

        for order in orders:
            self._add_order_card(order)
