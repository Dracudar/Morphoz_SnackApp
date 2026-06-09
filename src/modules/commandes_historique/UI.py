#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI.py - Vue historique des commandes

Description:
    Interface Qt/PySide6 de consultation de l'historique des commandes.
    Affiche toutes les commandes (en cours, terminées, annulées) sauf celles
    en cours de saisie et les fichiers corrompus.
    La recherche libre reste accessible en permanence ; les filtres avancés
    (statut, période, type de plat) sont regroupés dans une fenêtre dédiée.

Author :
    Dracudar

Version:
    3.0

Date de création :
    2026.05.26

Date de modification:
    2026.06.09
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QPushButton,
	QScrollArea,
	QVBoxLayout,
	QWidget,
)

from src.backend.data_sources import get_all_history_orders
from src.modules.commandes_historique.filtre_dialog import FiltreHistoriqueDialog


# ── Couleurs (identiques à conteneur_suivi_commande) ─────────────────────────
_BG_MAIN       = "#2f3136"
_BG_CARD       = "#3a3d43"
_BG_PLAT       = "#4a4e55"
_BORDER_CARD   = "#7f7f7f"
_BORDER_PLAT   = "#60646c"
_TEXT_TITLE    = "#f5f5f5"
_TEXT_CARD_ID  = "#f5f5f5"
_TEXT_CARD_CNT = "#a8acb3"
_TEXT_PLAT     = "#d6d6d6"

# ── Badges statut plat ───────────────────────────────────────────────────────
_STATUTS_PLAT: Dict[str, tuple] = {
	"en préparation": ("#7a4a1a", "#c97a30", "En prép."),
	"prêt":           ("#5e4a00", "#d4a017", "Prêt"),
	"livré":          ("#1a5e2a", "#4caf50", "Livré"),
	"annulé":         ("#5e1a1a", "#c0392b", "Annulé"),
}

# ── Badges statut commande ───────────────────────────────────────────────────
_STATUTS_COMMANDE: Dict[str, tuple] = {
	"validée":  ("#7a4a1a", "#c97a30", "En cours"),
	"terminée": ("#1a5e2a", "#4caf50", "Terminée"),
	"annulée":  ("#5e1a1a", "#c0392b", "Annulée"),
}

# ── Labels statut pour l'indicateur de filtres actifs ────────────────────────
_STATUT_LABELS = {"validée": "En cours", "terminée": "Terminée", "annulée": "Annulée"}

# ── État de filtres par défaut (aucun filtre actif) ──────────────────────────
_FILTERS_DEFAULT: Dict[str, Any] = {
	"status":     None,
	"date_from":  "",
	"time_from":  "",
	"date_to":    "",
	"time_to":    "",
	"plat_types": set(),
}


class CommandesHistoriqueModule(QFrame):
	"""Module de consultation de l'historique de toutes les commandes."""

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

		# Ligne : recherche + bouton filtres + rafraîchir
		search_row = QHBoxLayout()
		self.search_field = QLineEdit()
		self.search_field.setPlaceholderText("Rechercher par ID, plat ou statut…")
		self.search_field.textChanged.connect(self.refresh_orders)

		self.filter_btn = QPushButton("⚙ Filtres")
		self.filter_btn.setObjectName("filterOpenButton")
		self.filter_btn.clicked.connect(self._open_filter_dialog)

		self.reload_button = QPushButton("↻ Rafraîchir")
		self.reload_button.setObjectName("reloadButton")
		self.reload_button.clicked.connect(self.refresh_orders)

		search_row.addWidget(self.search_field, 1)
		search_row.addWidget(self.filter_btn)
		search_row.addWidget(self.reload_button)
		main_layout.addLayout(search_row)

		# Indicateur de filtres actifs (masqué par défaut)
		self.filter_indicator = QLabel("")
		self.filter_indicator.setObjectName("filterIndicator")
		self.filter_indicator.setVisible(False)
		main_layout.addWidget(self.filter_indicator)

		# Compteur
		self.summary_label = QLabel("Commandes : 0")
		self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.summary_label.setStyleSheet(
			f"color: {_TEXT_CARD_CNT}; font-size: 13px; font-weight: 600;"
		)
		main_layout.addWidget(self.summary_label)

		# Zone scrollable
		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
		self.scroll_area.setStyleSheet(
			f"QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: {_BG_MAIN}; }}"
		)
		main_layout.addWidget(self.scroll_area, 1)

		self.list_container = QWidget()
		self.list_layout = QVBoxLayout(self.list_container)
		self.list_layout.setContentsMargins(0, 0, 0, 0)
		self.list_layout.setSpacing(8)
		self.list_layout.addStretch()
		self.scroll_area.setWidget(self.list_container)

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
			QLineEdit {{
				background-color: #3b3f46;
				color: {_TEXT_TITLE};
				border: 1px solid #676d79;
				border-radius: 6px;
				padding: 6px 8px;
			}}
			QPushButton#reloadButton {{
				background-color: #4f545e;
				border: 1px solid #7d8390;
				border-radius: 7px;
				color: {_TEXT_TITLE};
				font-size: 14px;
				font-weight: 700;
				min-height: 34px;
				padding: 6px 12px;
			}}
			QPushButton#reloadButton:hover {{
				background-color: #626978;
			}}
			QPushButton#filterOpenButton {{
				background-color: #4f545e;
				border: 1px solid #7d8390;
				border-radius: 7px;
				color: {_TEXT_TITLE};
				font-size: 14px;
				font-weight: 700;
				min-height: 34px;
				padding: 6px 12px;
			}}
			QPushButton#filterOpenButton:hover {{
				background-color: #626978;
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
		if f.get("date_from") or f.get("date_to"):
			n += 1
		if f.get("plat_types"):
			n += 1
		return n

	def _update_filter_indicator(self):
		"""Met à jour le bouton filtres et l'indicateur textuel selon l'état actif."""
		n = self._count_active_filters()
		if n > 0:
			self.filter_btn.setText(f"⚙ Filtres · {n} actif{'s' if n > 1 else ''}")
			self.filter_btn.setStyleSheet(
				"""
				QPushButton#filterOpenButton {
					background-color: #4a3a1a;
					border: 1px solid #c97a30;
					border-radius: 7px;
					color: #c97a30;
					font-size: 14px;
					font-weight: 700;
					min-height: 34px;
					padding: 6px 12px;
				}
				QPushButton#filterOpenButton:hover { background-color: #5a4a2a; }
				"""
			)
			self.filter_indicator.setText(self._describe_active_filters())
			self.filter_indicator.setVisible(True)
		else:
			self.filter_btn.setText("⚙ Filtres")
			self.filter_btn.setStyleSheet("")
			self.filter_indicator.setVisible(False)

	def _describe_active_filters(self) -> str:
		"""Construit un résumé textuel des filtres actifs pour l'indicateur."""
		f = self._filters
		parts = []
		if f.get("status"):
			parts.append(_STATUT_LABELS.get(f["status"], f["status"]))
		date_from, time_from = f.get("date_from", ""), f.get("time_from", "")
		date_to, time_to = f.get("date_to", ""), f.get("time_to", "")
		if date_from or date_to:
			from_str = f"{date_from} {time_from}".strip() if date_from else "…"
			to_str = f"{date_to} {time_to}".strip() if date_to else "…"
			parts.append(f"{from_str} → {to_str}")
		plat_types = f.get("plat_types") or set()
		if plat_types:
			parts.append(", ".join(sorted(plat_types)))
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
		orders = get_all_history_orders()
		f = self._filters

		# Filtre statut
		if f.get("status") is not None:
			orders = [o for o in orders if o.get("status", "").lower() == f["status"]]

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

		# Filtre type de plat
		active_types: Set[str] = set(f.get("plat_types") or set())
		if active_types:
			orders = [
				o for o in orders
				if any(item.get("plat", "").strip() in active_types for item in o.get("items", []))
			]

		# Filtre recherche libre
		query = self.search_field.text().strip().lower()
		if query:
			orders = [o for o in orders if self._matches_search(o, query)]

		self.clear_cards()
		self.summary_label.setText(f"Commandes : {len(orders)}")

		if not orders:
			empty = QLabel("Aucune commande trouvée.")
			empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
			empty.setStyleSheet(f"color: {_TEXT_CARD_CNT}; font-size: 14px; padding: 20px;")
			self.list_layout.insertWidget(0, empty)
			return

		for order in orders:
			self._add_order_card(order)

	# ── Construction des cartes ─────────────────────────────────────────────

	def _add_order_card(self, order: Dict[str, Any]):
		order_id = order.get("id", "")
		is_collapsed = order_id not in self._expanded_orders

		card = QFrame()
		card.setObjectName("commandeCard")
		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(8, 8, 8, 8)
		card_layout.setSpacing(6)

		plats_container = QWidget()
		plats_layout = QVBoxLayout(plats_container)
		plats_layout.setContentsMargins(0, 0, 0, 0)
		plats_layout.setSpacing(4)

		for item in order.get("items", []):
			plats_layout.addWidget(self._build_plat_subcard(item))

		card_layout.addWidget(self._build_card_header(order, plats_container, is_collapsed))
		card_layout.addWidget(plats_container)
		plats_container.setVisible(not is_collapsed)

		card.setStyleSheet(
			f"""
			QFrame#commandeCard {{
				background-color: {_BG_CARD};
				border: 1px solid {_BORDER_CARD};
				border-radius: 8px;
			}}
			"""
		)

		self.list_layout.insertWidget(self.list_layout.count() - 1, card)

	def _build_card_header(
		self, order: Dict[str, Any], plats_container: QWidget, is_collapsed: bool
	) -> QFrame:
		header = QFrame()
		header.setObjectName("commandeCardHeader")
		header_layout = QHBoxLayout(header)
		header_layout.setContentsMargins(0, 0, 0, 0)
		header_layout.setSpacing(8)

		order_id = order.get("id", "")

		toggle_btn = QPushButton("▶" if is_collapsed else "▼")
		toggle_btn.setFixedSize(20, 20)
		toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
		toggle_btn.setStyleSheet(
			f"QPushButton {{ color: {_TEXT_CARD_CNT}; background: transparent; border: none; font-size: 11px; }}"
			f"QPushButton:hover {{ color: {_TEXT_CARD_ID}; }}"
		)
		toggle_btn.clicked.connect(lambda: self._toggle_order(order_id, plats_container, toggle_btn))
		header_layout.addWidget(toggle_btn)

		priority_slot = QLabel("!" if order.get("priority", False) else "")
		priority_slot.setFixedWidth(16)
		priority_slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
		priority_slot.setStyleSheet(
			"color: #e74c3c; font-size: 16px; font-weight: 900; padding: 0;"
		)
		header_layout.addWidget(priority_slot)

		id_label = QLabel(order_id)
		id_label.setStyleSheet(f"color: {_TEXT_CARD_ID}; font-size: 14px; font-weight: 700;")
		header_layout.addWidget(id_label)

		header_layout.addWidget(self._build_order_status_badge(order.get("status", "")))

		amount = order.get("amount")
		amount_label = QLabel(f"{amount:.2f} €" if isinstance(amount, (int, float)) else "-")
		amount_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 13px; font-weight: 600;")
		header_layout.addWidget(amount_label)

		header_layout.addStretch()

		date_str = self._format_date(order.get("created_at", ["", ""]))
		if date_str and date_str != "-":
			date_label = QLabel(f"Créé : {date_str}")
			date_label.setStyleSheet(f"color: {_TEXT_CARD_CNT}; font-size: 11px;")
			header_layout.addWidget(date_label)

		return header

	def _toggle_order(self, order_id: str, plats_container: QWidget, toggle_btn: QPushButton):
		if order_id in self._expanded_orders:
			self._expanded_orders.discard(order_id)
			plats_container.setVisible(False)
			toggle_btn.setText("▶")
		else:
			self._expanded_orders.add(order_id)
			plats_container.setVisible(True)
			toggle_btn.setText("▼")

	def _build_plat_subcard(self, item: Dict[str, Any]) -> QFrame:
		subcard = QFrame()
		subcard.setObjectName("platSubCard")
		subcard_layout = QHBoxLayout(subcard)
		subcard_layout.setContentsMargins(8, 4, 8, 4)
		subcard_layout.setSpacing(8)

		full_id = item.get("id", "")
		plat_id_reduit = full_id.rsplit("-", 1)[-1] if "-" in full_id else full_id
		id_label = QLabel(plat_id_reduit)
		id_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 13px; font-weight: 500;")
		subcard_layout.addWidget(id_label)

		nom = item.get("nom") or item.get("plat") or ""
		if nom:
			nom_label = QLabel(nom)
			nom_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 12px;")
			subcard_layout.addWidget(nom_label, 1)
		else:
			subcard_layout.addStretch(1)

		subcard_layout.addWidget(self._build_plat_status_badge(item.get("status", "")))

		subcard.setStyleSheet(
			f"""
			QFrame#platSubCard {{
				background-color: {_BG_PLAT};
				border: 1px solid {_BORDER_PLAT};
				border-radius: 4px;
			}}
			"""
		)
		return subcard

	def _build_plat_status_badge(self, status: str) -> QLabel:
		key = status.lower()
		bg, fg, label_text = _STATUTS_PLAT.get(key, ("#3a3d43", "#7a7f87", status or "?"))
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
				padding: 1px 6px;
			}}
			"""
		)
		return badge

	def _build_order_status_badge(self, status: str) -> QLabel:
		key = status.lower()
		bg, fg, label_text = _STATUTS_COMMANDE.get(key, ("#3a3d43", "#7a7f87", status or "?"))
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

	def _format_date(self, value: Any) -> str:
		if isinstance(value, list) and len(value) >= 2:
			return f"{value[0]} {value[1]}".strip()
		if isinstance(value, str):
			return value
		return "-"
