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
    Pour les commandes "validées", des boutons permettent de changer le statut
    des plats "en préparation" ou "prêts" (→ Prêt, → Livré, annuler) et de
    réimprimer les tickets récap (par commande) ou cuisine (par plat).
    Un bouton global en bas à droite réimprime tous les tickets cuisine actifs.

Author :
    Dracudar

Version:
    3.8

Date de création :
    2026.05.26

Date de modification:
    2026.06.21
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMessageBox,
	QPushButton,
	QVBoxLayout,
	QWidget,
)

from src.utils.tactile import EnTeteCliquable, ScrollAreaTactile
from src.UI.utils.icones import icone, icone_action
from src.backend.app_config import get_print_options
from src.backend.data_sources import get_all_history_orders
from src.backend.printer import reprint_all_active_cuisine, reprint_ticket_cuisine_plat, reprint_ticket_recap
from src.modules.commandes_historique.filtre_dialog import FiltreHistoriqueDialog
from src.modules.commandes_suivi.backend.commandes_suivi_gestion import (
	annuler_commande_complete,
	annuler_plat_valide,
	marquer_plat_livre,
	marquer_plat_pret,
	retour_preparation,
	retour_pret,
)


# ── Styles des boutons d'action dans les sous-cartes plat ───────────────────
_STYLE_BTN_PRET = (
	"QPushButton { background-color: #4a3a00; color: #d4a017; border: 1px solid #d4a017;"
	" border-radius: 3px; font-size: 11px; font-weight: 600; padding: 2px 6px; min-height: 22px; }"
	" QPushButton:hover { background-color: #5a4a10; }"
)
_STYLE_BTN_LIVRE = (
	"QPushButton { background-color: #1a4a2a; color: #4caf50; border: 1px solid #4caf50;"
	" border-radius: 3px; font-size: 11px; font-weight: 600; padding: 2px 6px; min-height: 22px; }"
	" QPushButton:hover { background-color: #2a6a3a; }"
)
_STYLE_BTN_ANNULER_PLAT = (
	"QPushButton { background-color: #d9534f; border: 1px solid #ac2925;"
	" border-radius: 4px; padding: 2px 4px; min-width: 24px; min-height: 22px; }"
	" QPushButton:hover:enabled { background-color: #c9302c; }"
	" QPushButton:disabled { background-color: #3b3f46; border: 1px solid #4a4e55; }"
)
_STYLE_BTN_CANCEL_CMD = (
	"QPushButton { background-color: #d9534f; border: 1px solid #ac2925;"
	" border-radius: 4px; padding: 2px 4px; min-width: 26px; min-height: 26px; }"
	" QPushButton:hover:enabled { background-color: #c9302c; }"
	" QPushButton:disabled { background-color: #3b3f46; border: 1px solid #4a4e55; }"
)
_STYLE_BTN_PRINT = (
	"QPushButton { background-color: #3d5068; border: 1px solid #5a80a8; border-radius: 4px;"
	" padding: 2px 4px; min-width: 26px; min-height: 26px; }"
	" QPushButton:hover:enabled { background-color: #4a6a90; }"
	" QPushButton:disabled { background-color: #3b3f46; border: 1px solid #4a4e55; }"
)
_STYLE_BTN_RETOUR = (
	"QPushButton { background-color: #28292f; color: #9098a8; border: 1px solid #4a5060;"
	" border-radius: 3px; font-size: 11px; font-weight: 600; padding: 2px 4px; min-height: 22px; }"
	" QPushButton:hover { background-color: #32343c; color: #b0b8c8; border-color: #606878; }"
)


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
	"non livré":      ("#3d1a5e", "#9b59b6", "Non livré"),
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
	"status":        None,
	"date_from":     "",
	"time_from":     "",
	"date_to":       "",
	"time_to":       "",
	"plat_types":    set(),
	"plat_statuses": set(),
	"priority_only": False,
}


class CommandesHistoriqueModule(QFrame):
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
		self.filter_btn.setIcon(icone("filter.svg", 16))
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
		self.back_button.setIcon(icone("return.svg", 18))
		self.back_button.setIconSize(QSize(18, 18))
		self.back_button.clicked.connect(self.go_back.emit)

		self.summary_label = QLabel("Commandes : 0  ·  Plats : 0")
		self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.summary_label.setObjectName("summaryLabel")

		self.print_all_btn = QPushButton("  Tickets cuisine (en cours)")
		self.print_all_btn.setObjectName("printAllButton")
		self.print_all_btn.setIcon(icone("print.svg", 16))
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

	# ── Construction des cartes ─────────────────────────────────────────────

	def _add_order_card(self, order: Dict[str, Any]):
		order_id = order.get("id", "")
		is_collapsed = order_id not in self._expanded_orders

		card = QFrame()
		card.setObjectName("commandeCard")
		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(8, 8, 8, 8)
		card_layout.setSpacing(6)

		# Contenu dépliable : panneau d'infos + sous-cartes plats
		content_container = QWidget()
		content_layout = QVBoxLayout(content_container)
		content_layout.setContentsMargins(0, 0, 0, 0)
		content_layout.setSpacing(4)

		content_layout.addWidget(self._build_order_info_panel(order))
		for item in order.get("items", []):
			content_layout.addWidget(self._build_plat_subcard(item, order))

		card_layout.addWidget(self._build_card_header(order, content_container, is_collapsed))
		card_layout.addWidget(content_container)
		content_container.setVisible(not is_collapsed)

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
		self, order: Dict[str, Any], content_container: QWidget, is_collapsed: bool
	) -> EnTeteCliquable:
		header = EnTeteCliquable()
		header.setObjectName("commandeCardHeader")
		header_layout = QHBoxLayout(header)
		header_layout.setContentsMargins(0, 0, 0, 0)
		header_layout.setSpacing(8)

		order_id = order.get("id", "")

		toggle_btn = QPushButton("▶" if is_collapsed else "▼")
		toggle_btn.setFixedSize(20, 20)
		toggle_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
		toggle_btn.setStyleSheet(
			f"QPushButton {{ color: {_TEXT_CARD_CNT}; background: transparent; border: none; font-size: 11px; }}"
		)
		header_layout.addWidget(toggle_btn)

		header.clicked.connect(lambda: self._toggle_order(order_id, content_container, toggle_btn))

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

		header_layout.addStretch()

		header_layout.addWidget(self._build_order_status_badge(order.get("status", "")))

		# Bouton annulation commande (avant le bouton impression)
		order_status = (order.get("status") or "").lower()
		btn_cancel_cmd = QPushButton()
		btn_cancel_cmd.setIcon(icone_action("cancel.svg", 14, "white", "#595d64"))
		btn_cancel_cmd.setIconSize(QSize(14, 14))
		btn_cancel_cmd.setToolTip("Annuler la commande")
		btn_cancel_cmd.setEnabled(order_status == "validée")
		btn_cancel_cmd.setStyleSheet(_STYLE_BTN_CANCEL_CMD)
		btn_cancel_cmd.clicked.connect(lambda _, o=order: self._on_annuler_commande(o))
		header_layout.addWidget(btn_cancel_cmd)

		# Bouton impression ticket récap (le plus à droite, désactivé si impression globalement off)
		options = get_print_options()
		btn_recap = QPushButton()
		btn_recap.setIcon(icone("print.svg", 14))
		btn_recap.setIconSize(QSize(14, 14))
		btn_recap.setToolTip("Réimprimer ticket récap" if options["impression_active"] else "Impression désactivée")
		btn_recap.setEnabled(options["impression_active"])
		btn_recap.setStyleSheet(_STYLE_BTN_PRINT)
		btn_recap.clicked.connect(lambda _, o=order: self._on_print_recap(o))
		header_layout.addWidget(btn_recap)

		return header

	def _toggle_order(self, order_id: str, content_container: QWidget, toggle_btn: QPushButton):
		if order_id in self._expanded_orders:
			self._expanded_orders.discard(order_id)
			content_container.setVisible(False)
			toggle_btn.setText("▶")
		else:
			self._expanded_orders.add(order_id)
			content_container.setVisible(True)
			toggle_btn.setText("▼")

	def _build_order_info_panel(self, order: Dict[str, Any]) -> QFrame:
		"""Panneau de synthèse affiché en haut du bloc déplié."""
		panel = QFrame()
		panel.setObjectName("orderInfoPanel")
		layout = QHBoxLayout(panel)
		layout.setContentsMargins(6, 6, 6, 6)
		layout.setSpacing(0)

		status = (order.get("status") or "").lower()
		nb_plats = len(order.get("items", []))
		amount = order.get("amount")
		payment = order.get("payment_type") or ""
		created = self._format_date(order.get("created_at", ["", ""]))
		delivery = self._format_date(order.get("finalization_at", ["", ""]))
		cancelled = self._format_date(order.get("cancelled_at", ["", ""]))

		infos = [
			("Plats", str(nb_plats)),
			("Montant", f"{amount:.2f} €" if isinstance(amount, (int, float)) else "-"),
		]
		if payment:
			infos.append(("Paiement", payment))
		if created:
			infos.append(("Créé", created))
		if status == "terminée" and delivery:
			infos.append(("Finalisé", delivery))
		if status == "annulée" and cancelled:
			infos.append(("Annulé", cancelled))

		for i, (key, value) in enumerate(infos):
			if i > 0:
				sep = QLabel("·")
				sep.setStyleSheet(f"color: {_BORDER_PLAT}; font-size: 13px; padding: 0 10px;")
				layout.addWidget(sep)
			key_w = QLabel(f"{key} :")
			key_w.setStyleSheet(f"color: {_TEXT_CARD_CNT}; font-size: 12px;")
			val_w = QLabel(value)
			val_w.setStyleSheet(
				f"color: {_TEXT_PLAT}; font-size: 12px; font-weight: 600; margin-left: 4px;"
			)
			layout.addWidget(key_w)
			layout.addWidget(val_w)

		layout.addStretch()

		panel.setStyleSheet(
			f"""
			QFrame#orderInfoPanel {{
				background-color: #353840;
				border: 1px solid {_BORDER_PLAT};
				border-radius: 4px;
			}}
			"""
		)
		return panel

	def _build_plat_subcard(self, item: Dict[str, Any], order: Dict[str, Any]) -> QFrame:
		order_status = (order.get("status") or "").lower()
		item_status = (item.get("status") or "").lower()
		is_active_order = order_status == "validée"
		is_terminal_item = item_status in ("livré", "annulé")
		show_pret = is_active_order and item_status == "en préparation"
		show_livre = is_active_order and item_status in ("en préparation", "prêt")
		show_retour_preparation = is_active_order and item_status == "prêt"
		show_retour_pret = item_status == "livré" and order_status in ("validée", "terminée")

		options = get_print_options()
		print_enabled = options["impression_active"] and not is_terminal_item

		subcard = QFrame()
		subcard.setObjectName("platSubCard")
		outer_layout = QVBoxLayout(subcard)
		outer_layout.setContentsMargins(8, 4, 8, 4)
		outer_layout.setSpacing(0)

		# ── Ligne : ID, Nom, Badge, boutons d'action, impression (le plus à droite) ──
		main_row = QHBoxLayout()
		main_row.setContentsMargins(0, 0, 0, 0)
		main_row.setSpacing(6)

		full_id = item.get("id", "")
		plat_id_reduit = full_id.rsplit("-", 1)[-1] if "-" in full_id else full_id
		id_label = QLabel(plat_id_reduit)
		id_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 13px; font-weight: 500;")
		main_row.addWidget(id_label)

		nom = item.get("nom") or item.get("plat") or ""
		if nom:
			nom_label = QLabel(nom)
			nom_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 12px;")
			main_row.addWidget(nom_label, 1)
		else:
			main_row.addStretch(1)

		# Zone d'action à largeur fixe : [← retour | badge | → Prêt | → Livré]
		# Chaque slot est soit un bouton soit un QWidget vide de même largeur → layout stable.

		# Slot retour (62px)
		if show_retour_preparation:
			btn_retour = QPushButton("← Prépa")
			btn_retour.setFixedWidth(62)
			btn_retour.setStyleSheet(_STYLE_BTN_RETOUR)
			btn_retour.setToolTip("Retour au statut En préparation")
			btn_retour.clicked.connect(lambda _, o=order, i=item: self._on_retour_preparation(o, i))
			main_row.addWidget(btn_retour)
		elif show_retour_pret:
			btn_retour = QPushButton("← Prêt")
			btn_retour.setFixedWidth(62)
			btn_retour.setStyleSheet(_STYLE_BTN_RETOUR)
			btn_retour.setToolTip("Retour au statut Prêt (peut rouvrir la commande si terminée)")
			btn_retour.clicked.connect(lambda _, o=order, i=item: self._on_retour_pret(o, i))
			main_row.addWidget(btn_retour)
		else:
			sp_retour = QWidget()
			sp_retour.setFixedWidth(62)
			main_row.addWidget(sp_retour)

		# Badge statut (68px)
		badge = self._build_plat_status_badge(item.get("status", ""))
		badge.setFixedWidth(68)
		main_row.addWidget(badge)

		# Slot → Prêt (62px)
		if show_pret:
			btn_pret = QPushButton("→ Prêt")
			btn_pret.setFixedWidth(62)
			btn_pret.setStyleSheet(_STYLE_BTN_PRET)
			btn_pret.setToolTip("Passer ce plat au statut Prêt")
			btn_pret.clicked.connect(lambda _, o=order, i=item: self._on_marquer_pret(o, i))
			main_row.addWidget(btn_pret)
		else:
			sp_pret = QWidget()
			sp_pret.setFixedWidth(62)
			main_row.addWidget(sp_pret)

		# Slot → Livré (62px)
		if show_livre:
			btn_livre = QPushButton("→ Livré")
			btn_livre.setFixedWidth(62)
			btn_livre.setStyleSheet(_STYLE_BTN_LIVRE)
			btn_livre.setToolTip("Passer ce plat au statut Livré")
			btn_livre.clicked.connect(lambda _, o=order, i=item: self._on_marquer_livre(o, i))
			main_row.addWidget(btn_livre)
		else:
			sp_livre = QWidget()
			sp_livre.setFixedWidth(62)
			main_row.addWidget(sp_livre)

		# Bouton annulation plat (toujours affiché pour commandes validées, désactivé si terminal)
		if is_active_order:
			btn_annuler = QPushButton()
			btn_annuler.setIcon(icone_action("cancel.svg", 12, "white", "#595d64"))
			btn_annuler.setIconSize(QSize(12, 12))
			btn_annuler.setToolTip("Annuler ce plat")
			btn_annuler.setEnabled(not is_terminal_item)
			btn_annuler.setStyleSheet(_STYLE_BTN_ANNULER_PLAT)
			btn_annuler.clicked.connect(lambda _, o=order, i=item: self._on_annuler_plat(o, i))
			main_row.addWidget(btn_annuler)

		# Bouton impression cuisine (le plus à droite, désactivé si terminal ou impression off)
		btn_print = QPushButton()
		btn_print.setIcon(icone("print.svg", 12))
		btn_print.setIconSize(QSize(12, 12))
		btn_print.setToolTip(
			"Réimprimer ticket cuisine pour ce plat" if print_enabled else "Impression désactivée"
		)
		btn_print.setEnabled(print_enabled)
		btn_print.setStyleSheet(_STYLE_BTN_PRINT)
		btn_print.clicked.connect(lambda _, o=order, i=item: self._on_print_cuisine_plat(o, i))
		main_row.addWidget(btn_print)

		outer_layout.addLayout(main_row)

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

	# ── Actions sur les commandes / plats ───────────────────────────────────

	def _on_print_recap(self, order: Dict[str, Any]):
		"""Réimprime le ticket récapitulatif de la commande."""
		try:
			reprint_ticket_recap(str(order["file"]))
		except Exception as e:
			QMessageBox.warning(self, "Impression", f"Erreur d'impression :\n{e}")

	def _on_print_cuisine_plat(self, order: Dict[str, Any], item: Dict[str, Any]):
		"""Réimprime le ticket cuisine d'un plat spécifique."""
		try:
			reprint_ticket_cuisine_plat(str(order["file"]), item["id"])
		except Exception as e:
			QMessageBox.warning(self, "Impression", f"Erreur d'impression :\n{e}")

	def _on_print_all_active(self):
		"""Imprime les tickets cuisine de tous les plats en préparation ou prêts."""
		try:
			count = reprint_all_active_cuisine()
			if count == 0:
				QMessageBox.information(self, "Impression", "Aucun plat en préparation ou prêt.")
			else:
				QMessageBox.information(
					self,
					"Impression",
					f"{count} ticket{'s' if count > 1 else ''} cuisine imprimé{'s' if count > 1 else ''}.",
				)
		except Exception as e:
			QMessageBox.warning(self, "Impression", f"Erreur d'impression :\n{e}")

	def _on_marquer_pret(self, order: Dict[str, Any], item: Dict[str, Any]):
		"""Passe le plat au statut Prêt et rafraîchit l'affichage."""
		marquer_plat_pret(str(order["file"]), item["id"])
		self.refresh_orders()

	def _on_marquer_livre(self, order: Dict[str, Any], item: Dict[str, Any]):
		"""Passe le plat directement au statut Livré (depuis En préparation ou Prêt) et rafraîchit."""
		marquer_plat_livre(str(order["file"]), item["id"])
		self.refresh_orders()

	def _on_annuler_plat(self, order: Dict[str, Any], item: Dict[str, Any]):
		"""Demande confirmation puis annule le plat avec horodatage."""
		nom_plat = item.get("nom") or item.get("plat") or item["id"]
		reponse = QMessageBox.question(
			self,
			"Confirmer l'annulation",
			f"Annuler le plat « {nom_plat} » ?",
			QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
		)
		if reponse == QMessageBox.StandardButton.Yes:
			annuler_plat_valide(str(order["file"]), item["id"])
			self.refresh_orders()

	def _on_annuler_commande(self, order: Dict[str, Any]):
		"""Demande confirmation puis annule tous les plats restants de la commande."""
		reponse = QMessageBox.question(
			self,
			"Confirmer l'annulation",
			f"Annuler tous les plats restants de la commande « {order.get('id', '')} » ?",
			QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
		)
		if reponse == QMessageBox.StandardButton.Yes:
			annuler_commande_complete(str(order["file"]))
			self.refresh_orders()

	def _on_retour_preparation(self, order: Dict[str, Any], item: Dict[str, Any]):
		"""Retour du statut Prêt à En préparation (correction cuisine)."""
		retour_preparation(None, str(order["file"]), item["id"], lambda _: None)
		self.refresh_orders()

	def _on_retour_pret(self, order: Dict[str, Any], item: Dict[str, Any]):
		"""Retour du statut Livré à Prêt, avec confirmation si la commande était terminée."""
		nom_plat = item.get("nom") or item.get("plat") or item["id"]
		reponse = QMessageBox.question(
			self,
			"Confirmer le retour",
			f"Ramener le plat « {nom_plat} » au statut Prêt ?\n"
			"Si la commande est terminée, elle sera réouverte.",
			QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
		)
		if reponse == QMessageBox.StandardButton.Yes:
			retour_pret(str(order["file"]), item["id"])
			self.refresh_orders()
