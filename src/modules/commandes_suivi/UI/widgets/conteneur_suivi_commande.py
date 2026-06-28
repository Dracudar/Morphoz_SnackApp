#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conteneur_suivi_commande.py - Widget suivi commandes

Description:
	Conteneur de suivi des commandes en préparation pour la colonne droite.
	Affiche un bloc par commande avec son ID, le nombre de plats en cours,
	et un sous-conteneur par plat (non annulé) avec son ID réduit et son statut.

Author :
    Dracudar

Version:
    1.4

Date de création :
    2026.05.18

Date de modification:
    2026.06.08
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QPushButton,
	QVBoxLayout,
	QWidget,
)

from src.utils.tactile import EnTeteCliquable, ScrollAreaTactile
from src.backend.data_sources import get_live_orders, signature_live_orders


# ── Couleurs ────────────────────────────────────────────────────────────────
_BG_MAIN        = "#2f3136"
_BG_CARD        = "#3a3d43"
_BG_PLAT        = "#4a4e55"
_BG_PLAT_ATTÉNUÉ = "#3a3d43"
_BORDER_CARD    = "#7f7f7f"
_BORDER_PLAT    = "#60646c"
_TEXT_TITLE     = "#f5f5f5"
_TEXT_CARD_ID   = "#f5f5f5"
_TEXT_CARD_CNT  = "#a8acb3"
_TEXT_PLAT      = "#d6d6d6"
_TEXT_PLAT_ATTÉNUÉ = "#7a7f87"

# ── Badges de statut ─────────────────────────────────────────────────────────
_STATUTS = {
    "en préparation": ("#7a4a1a", "#c97a30", "En prép."),
    "prêt":           ("#5e4a00", "#d4a017", "Prêt"),
    "livré":          ("#1a5e2a", "#4caf50", "Livré"),
    "annulé":         ("#5e1a1a", "#c0392b", "Annulé"),
}


class ConteneurSuiviCommande(QFrame):
	"""Affiche et rafraichit la liste des commandes en preparation."""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("suiviContainer")
		self._expanded_orders: set[str] = set()
		# État du rafraîchissement incrémental
		self._last_signature = None              # signature du dossier au dernier refresh
		self._cards: dict[str, QFrame] = {}      # carte affichée par ID de commande
		self._card_sigs: dict[str, tuple] = {}   # empreinte des données rendues par carte
		self._displayed_order: list[str] = []    # ordre des cartes actuellement affichées
		self._build_ui()
		self._build_timer()
		self.refresh_orders()

	# ── Construction de l'interface ─────────────────────────────────────────

	def _build_ui(self):
		"""Construit l'interface : titre compteur, zone scrollable et style."""
		self.setFrameShape(QFrame.Shape.StyledPanel)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(10, 10, 10, 10)
		main_layout.setSpacing(8)

		self.title_label = QLabel("Commandes en préparation : 0")
		self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.title_label.setObjectName("suiviTitle")
		main_layout.addWidget(self.title_label)

		self.scroll_area = ScrollAreaTactile(_BG_MAIN)
		main_layout.addWidget(self.scroll_area)

		self.list_container = QWidget()
		self.list_layout = QVBoxLayout(self.list_container)
		self.list_layout.setContentsMargins(0, 0, 0, 0)
		self.list_layout.setSpacing(8)
		self.list_layout.addStretch()
		self.scroll_area.setWidget(self.list_container)

		self.setStyleSheet(
			f"""
			QFrame#suiviContainer {{
				background-color: {_BG_MAIN};
				border: 1px solid {_BORDER_CARD};
			}}
			QLabel#suiviTitle {{
				color: {_TEXT_TITLE};
				font-size: 17px;
				font-weight: 700;
				padding: 4px;
			}}
			"""
		)

	def _build_timer(self):
		"""Démarre un timer de rafraîchissement automatique toutes les 2 secondes."""
		self.refresh_timer = QTimer(self)
		self.refresh_timer.setInterval(2000)
		self.refresh_timer.timeout.connect(self.refresh_orders)
		self.refresh_timer.start()

	# ── Gestion des données ─────────────────────────────────────────────────

	def clear_orders(self):
		"""Supprime toutes les cartes de commande affichées dans la liste et l'état du diff."""
		while self.list_layout.count() > 1:
			item = self.list_layout.takeAt(0)
			widget = item.widget()
			if widget is not None:
				widget.deleteLater()
		self._cards.clear()
		self._card_sigs.clear()
		self._displayed_order.clear()

	@staticmethod
	def _order_signature(order: dict) -> tuple:
		"""Empreinte des données d'une commande effectivement rendues dans sa carte."""
		return (
			bool(order.get("priority", False)),
			order.get("pending_count", 0),
			tuple((it.get("id", ""), it.get("status", "")) for it in order.get("items", [])),
		)

	def refresh_orders(self):
		"""Rafraîchit la liste : court-circuit si rien n'a changé, sinon diff des seules cartes modifiées."""
		# Couche 2 — court-circuit : si le dossier en_cours est inchangé, ne rien faire.
		signature = signature_live_orders()
		if signature == self._last_signature:
			return
		self._last_signature = signature

		orders = get_live_orders()

		# Compteur (mis à jour à chaque refresh non court-circuité).
		total_files = len(orders)
		total_plats = sum(order.get("pending_count", 0) for order in orders)
		self.title_label.setText(
			f"Commandes : {total_files}  |  Plats en cours : {total_plats}"
		)

		# Couche 3 — diff : ne reconstruire que les cartes ajoutées ou modifiées.
		nouvel_ordre = [order.get("id", "") for order in orders]
		nouvel_ensemble = set(nouvel_ordre)

		# Suppressions : commandes qui ne sont plus en cours.
		for order_id in list(self._cards.keys()):
			if order_id not in nouvel_ensemble:
				ancienne = self._cards.pop(order_id)
				self.list_layout.removeWidget(ancienne)
				ancienne.deleteLater()
				self._card_sigs.pop(order_id, None)

		# Ajouts et modifications.
		for order in orders:
			order_id = order.get("id", "")
			sig = self._order_signature(order)
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
			# sinon : carte inchangée, on ne la touche pas.

		# Réordonnancement uniquement si la séquence a changé (déplacement de widgets, pas de reconstruction).
		if nouvel_ordre != self._displayed_order:
			for order_id in nouvel_ordre:
				self.list_layout.removeWidget(self._cards[order_id])
			for position, order_id in enumerate(nouvel_ordre):
				self.list_layout.insertWidget(position, self._cards[order_id])
			self._displayed_order = nouvel_ordre

	# ── Construction des cartes ─────────────────────────────────────────────

	def _build_order_card(self, order: dict) -> QFrame:
		"""Construit (sans l'insérer) le bloc d'une commande avec ses sous-conteneurs de plats."""
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
		plats_layout.setSpacing(6)

		visible_items = order.get("items", [])
		for item in visible_items:
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

		return card

	def _build_card_header(self, order: dict, plats_container: QWidget, is_collapsed: bool) -> EnTeteCliquable:
		"""Construit le bandeau d'en-tête cliquable sur toute sa largeur."""
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

		header.clicked.connect(lambda: self._toggle_order(order_id, plats_container, toggle_btn))

		priority_slot = QLabel("!" if order.get("priority", False) else "")
		priority_slot.setFixedWidth(16)
		priority_slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
		priority_slot.setStyleSheet(
			"color: #e74c3c; font-size: 16px; font-weight: 900; padding: 0;"
		)
		header_layout.addWidget(priority_slot)

		id_label = QLabel(order_id)
		id_label.setStyleSheet(
			f"color: {_TEXT_CARD_ID}; font-size: 14px; font-weight: 700;"
		)
		header_layout.addWidget(id_label, 1)

		count = order.get("pending_count", 0)
		plat_word = "plat" if count <= 1 else "plats"
		count_label = QLabel(f"{count} {plat_word} en cours")
		count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
		count_label.setStyleSheet(
			f"color: {_TEXT_CARD_CNT}; font-size: 12px; font-weight: 500;"
		)
		header_layout.addWidget(count_label)

		return header

	def _toggle_order(self, order_id: str, plats_container: QWidget, toggle_btn: QPushButton):
		"""Bascule l'état replié/déplié d'une commande et met à jour l'affichage."""
		if order_id in self._expanded_orders:
			self._expanded_orders.discard(order_id)
			plats_container.setVisible(False)
			toggle_btn.setText("▶")
		else:
			self._expanded_orders.add(order_id)
			plats_container.setVisible(True)
			toggle_btn.setText("▼")

	def _build_plat_subcard(self, item: dict) -> QFrame:
		"""Construit un sous-conteneur pour un plat avec son ID réduit et son badge de statut."""
		status = item.get("status", "").strip()
		status_key = status.lower()
		is_atténué = status_key in ("livré", "annulé")

		subcard = QFrame()
		subcard.setObjectName("platSubCard")
		subcard_layout = QHBoxLayout(subcard)
		subcard_layout.setContentsMargins(8, 4, 8, 4)
		subcard_layout.setSpacing(8)

		full_id = item.get("id", "")
		plat_id_reduit = full_id.rsplit("-", 1)[-1] if "-" in full_id else full_id
		text_color = _TEXT_PLAT_ATTÉNUÉ if is_atténué else _TEXT_PLAT
		id_label = QLabel(plat_id_reduit)
		id_label.setStyleSheet(
			f"color: {text_color}; font-size: 13px; font-weight: 500;"
		)
		subcard_layout.addWidget(id_label, 1)

		subcard_layout.addWidget(self._build_status_badge(status))

		bg = _BG_PLAT_ATTÉNUÉ if is_atténué else _BG_PLAT
		subcard.setStyleSheet(
			f"""
			QFrame#platSubCard {{
				background-color: {bg};
				border: 1px solid {_BORDER_PLAT};
				border-radius: 4px;
			}}
			"""
		)

		return subcard

	def _build_status_badge(self, status: str) -> QLabel:
		"""Retourne un QLabel stylisé en badge coloré selon le statut du plat."""
		key = status.lower()
		bg, fg, label_text = _STATUTS.get(key, ("#3a3d43", "#7a7f87", status or "?"))

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
