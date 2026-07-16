#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI_consultation.py - Vue historique en lecture seule (mode Gestion et statistiques)

Description:
    Affichage indépendant de l'historique des commandes, réservé au mode
    Gestion et statistiques : recherche et filtres avancés identiques à
    CommandesHistoriqueModule (mode Saisie/Gestion), mais aucune action
    (changement de statut, annulation, impression) — uniquement de la
    consultation. Le style des cartes reprend celui de ConteneurSuiviCommande
    (module commandes_suivi) : pas de colonnes réservées à des boutons, un
    badge de statut aligné à droite de chaque plat. En contrepartie, chaque
    plat affiche plus de détails (prix, horodatage de préparation/livraison/
    annulation) qu'un tableau de bord opérationnel n'a besoin d'afficher.

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

from datetime import datetime
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

from src.utils.tactile import EnTeteCliquable, ScrollAreaTactile
from src.UI.utils.icones import icone
from src.backend.data_sources import get_all_history_orders, signature_history_orders
from src.modules.commandes_historique.filtre_dialog import FiltreHistoriqueDialog


# ── Couleurs (identiques à commandes_historique/UI.py et conteneur_suivi_commande) ──
_BG_MAIN       = "#2f3136"
_BG_CARD       = "#3a3d43"
_BG_PLAT       = "#4a4e55"
_BORDER_CARD   = "#7f7f7f"
_BORDER_PLAT   = "#60646c"
_TEXT_TITLE    = "#f5f5f5"
_TEXT_CARD_ID  = "#f5f5f5"
_TEXT_CARD_CNT = "#a8acb3"
_TEXT_PLAT     = "#d6d6d6"
_TEXT_DETAIL   = "#9098a8"

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

# ── Libellé de l'horodatage affiché par plat, selon son statut ───────────────
_HORODATAGE_PAR_STATUT = {
	"prêt":      ("Prêt à", "ready_at"),
	"livré":     ("Livré à", "delivered_at"),
	"annulé":    ("Annulé à", "cancelled_at"),
}

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


class HistoriqueConsultationModule(QFrame):
	"""Consultation en lecture seule de l'historique des commandes (mode Gestion et statistiques)."""

	go_back = Signal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("historiqueConsultationModule")
		self._expanded_orders: set[str] = set()
		self._filters: Dict[str, Any] = dict(_FILTERS_DEFAULT)
		self._filters["plat_types"] = set()
		# État du rafraîchissement incrémental
		self._last_key = None                    # clé de court-circuit au dernier refresh
		self._cards: dict[str, QFrame] = {}      # carte affichée par ID de commande
		self._card_sigs: dict[str, tuple] = {}   # empreinte des données rendues par carte
		self._displayed_order: list[str] = []    # ordre des cartes affichées
		self._empty_label: QLabel | None = None  # label "aucune commande" éventuel
		self._build_ui()
		self._build_timer()
		self.refresh_orders()

	# ── Construction de l'interface ─────────────────────────────────────────

	def _build_ui(self):
		self.setFrameShape(QFrame.Shape.StyledPanel)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(14, 14, 14, 14)
		main_layout.setSpacing(8)

		title = QLabel("Historique des commandes")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setObjectName("sectionTitle")
		main_layout.addWidget(title)

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

		self.filter_indicator = QLabel("")
		self.filter_indicator.setObjectName("filterIndicator")
		self.filter_indicator.setVisible(False)
		main_layout.addWidget(self.filter_indicator)

		self.scroll_area = ScrollAreaTactile(_BG_MAIN)
		main_layout.addWidget(self.scroll_area, 1)

		self.list_container = QWidget()
		self.list_layout = QVBoxLayout(self.list_container)
		self.list_layout.setContentsMargins(0, 0, 0, 0)
		self.list_layout.setSpacing(8)
		self.list_layout.addStretch()
		self.scroll_area.setWidget(self.list_container)

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

		bottom_bar.addWidget(self.back_button)
		bottom_bar.addStretch()
		bottom_bar.addWidget(self.summary_label)
		bottom_bar.addStretch()
		main_layout.addLayout(bottom_bar)

		self.setStyleSheet(
			f"""
			QFrame#historiqueConsultationModule {{
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
		self._cards.clear()
		self._card_sigs.clear()
		self._displayed_order.clear()
		self._empty_label = None

	def _filters_snapshot(self) -> tuple:
		"""Capture hashable des filtres et de la recherche, pour le court-circuit."""
		f = self._filters
		return (
			f.get("status"),
			bool(f.get("priority_only")),
			f.get("date_from", ""), f.get("time_from", ""),
			f.get("date_to", ""), f.get("time_to", ""),
			frozenset(f.get("plat_types") or set()),
			frozenset(f.get("plat_statuses") or set()),
			self.search_field.text().strip().lower(),
		)

	def refresh_orders(self):
		# Court-circuit : la clé combine l'état des dossiers d'historique, les
		# filtres et la recherche (pas d'impression ici, contrairement au module
		# opérationnel — aucun bouton dont l'état dépend de la config imprimante).
		cle = (signature_history_orders(), self._filters_snapshot())
		if cle == self._last_key:
			return
		self._last_key = cle

		orders = get_all_history_orders()
		f = self._filters

		if f.get("status") is not None:
			orders = [o for o in orders if o.get("status", "").lower() == f["status"]]

		if f.get("priority_only"):
			orders = [o for o in orders if o.get("priority", False)]

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

		query = self.search_field.text().strip().lower()
		if query:
			orders = [o for o in orders if self._matches_search(o, query)]

		total_plats = sum(len(o.get("items", [])) for o in orders)
		self.summary_label.setText(f"Commandes : {len(orders)}  ·  Plats : {total_plats}")

		if self._empty_label is not None:
			self.list_layout.removeWidget(self._empty_label)
			self._empty_label.deleteLater()
			self._empty_label = None

		if not orders:
			self.clear_cards()
			self._empty_label = QLabel("Aucune commande trouvée.")
			self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
			self._empty_label.setStyleSheet(f"color: {_TEXT_CARD_CNT}; font-size: 14px; padding: 20px;")
			self.list_layout.insertWidget(0, self._empty_label)
			return

		nouvel_ordre = [o.get("id", "") for o in orders]
		nouvel_ensemble = set(nouvel_ordre)

		for order_id in list(self._cards.keys()):
			if order_id not in nouvel_ensemble:
				ancienne = self._cards.pop(order_id)
				self.list_layout.removeWidget(ancienne)
				ancienne.deleteLater()
				self._card_sigs.pop(order_id, None)

		for order in orders:
			order_id = order.get("id", "")
			sig = repr(order)
			if order_id not in self._cards:
				card = self._build_order_card(order)
				self._cards[order_id] = card
				self._card_sigs[order_id] = sig
				self.list_layout.insertWidget(self.list_layout.count() - 1, card)
			elif sig != self._card_sigs.get(order_id):
				ancienne = self._cards[order_id]
				index = self.list_layout.indexOf(ancienne)
				self.list_layout.removeWidget(ancienne)
				ancienne.deleteLater()
				card = self._build_order_card(order)
				self._cards[order_id] = card
				self._card_sigs[order_id] = sig
				self.list_layout.insertWidget(index, card)

		if nouvel_ordre != self._displayed_order:
			for order_id in nouvel_ordre:
				self.list_layout.removeWidget(self._cards[order_id])
			for position, order_id in enumerate(nouvel_ordre):
				self.list_layout.insertWidget(position, self._cards[order_id])
			self._displayed_order = nouvel_ordre

	# ── Construction des cartes ─────────────────────────────────────────────

	def _build_order_card(self, order: Dict[str, Any]) -> QFrame:
		order_id = order.get("id", "")
		is_collapsed = order_id not in self._expanded_orders

		card = QFrame()
		card.setObjectName("commandeCard")
		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(8, 8, 8, 8)
		card_layout.setSpacing(6)

		content_container = QWidget()
		content_layout = QVBoxLayout(content_container)
		content_layout.setContentsMargins(0, 0, 0, 0)
		content_layout.setSpacing(4)

		content_layout.addWidget(self._build_order_info_panel(order))
		for item in order.get("items", []):
			content_layout.addWidget(self._build_plat_subcard(item))

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

		return card

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
		header_layout.addWidget(id_label, 1)

		header_layout.addWidget(self._build_order_status_badge(order.get("status", "")))

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
		"""Panneau de synthèse affiché en haut du bloc déplié (détails côté "général")."""
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
			("Statut", _STATUTS_COMMANDE.get(status, (None, None, order.get("status") or "?"))[2]),
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

	def _build_plat_subcard(self, item: Dict[str, Any]) -> QFrame:
		"""Sous-carte plat : ID + nom à gauche, détails (prix, horodatage) et badge à droite.

		Reprend le principe de conteneur_suivi_commande (pas de colonnes réservées à
		des boutons puisqu'il n'y a aucune action ici) en ajoutant le détail que la
		vue opérationnelle n'a pas besoin d'afficher : prix et horodatage du plat.
		"""
		status = (item.get("status") or "").strip()
		status_key = status.lower()

		subcard = QFrame()
		subcard.setObjectName("platSubCard")
		row = QHBoxLayout(subcard)
		row.setContentsMargins(8, 6, 8, 6)
		row.setSpacing(10)

		full_id = item.get("id", "")
		plat_id_reduit = full_id.rsplit("-", 1)[-1] if "-" in full_id else full_id
		id_label = QLabel(plat_id_reduit)
		id_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 13px; font-weight: 500;")
		row.addWidget(id_label)

		nom = item.get("nom") or item.get("plat") or ""
		if nom:
			nom_label = QLabel(nom)
			nom_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 12px;")
			row.addWidget(nom_label, 1)
		else:
			row.addStretch(1)

		prix = item.get("price")
		if isinstance(prix, (int, float)):
			prix_label = QLabel(f"{prix:.2f} €")
			prix_label.setStyleSheet(f"color: {_TEXT_DETAIL}; font-size: 12px;")
			row.addWidget(prix_label)

		horodatage = self._format_horodatage(item, status_key)
		if horodatage:
			horaire_label = QLabel(horodatage)
			horaire_label.setStyleSheet(f"color: {_TEXT_DETAIL}; font-size: 12px;")
			row.addWidget(horaire_label)

		row.addWidget(self._build_plat_status_badge(status))

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

	def _format_horodatage(self, item: Dict[str, Any], status_key: str) -> str:
		"""Retourne "Prêt à HH:MM" / "Livré à HH:MM" / "Annulé à HH:MM" selon le statut du plat."""
		info = _HORODATAGE_PAR_STATUT.get(status_key)
		if info is None:
			return ""
		libelle, champ = info
		valeur = item.get(champ)
		if not isinstance(valeur, list) or len(valeur) < 2:
			return ""
		heure = str(valeur[1]).strip()
		if not heure:
			return ""
		return f"{libelle} {heure}"

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
