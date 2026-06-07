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
    1.2

Date de création :
    2026.05.18

Date de modification:
    2026.06.07
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QScrollArea,
	QVBoxLayout,
	QWidget,
)

from src.backend.data_sources import get_live_orders


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

		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
		self.scroll_area.setStyleSheet(
			f"QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: {_BG_MAIN}; }}"
		)
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
		"""Supprime toutes les cartes de commande affichées dans la liste."""
		while self.list_layout.count() > 1:
			item = self.list_layout.takeAt(0)
			widget = item.widget()
			if widget is not None:
				widget.deleteLater()

	def refresh_orders(self):
		"""Recharge les commandes en cours, met à jour le compteur et reconstruit la liste."""
		orders = get_live_orders()
		self.clear_orders()

		total_files = len(orders)
		total_plats = sum(order.get("pending_count", 0) for order in orders)
		self.title_label.setText(
			f"Commandes : {total_files}  |  Plats en cours : {total_plats}"
		)

		for order in orders:
			self._add_order_card(order)

	# ── Construction des cartes ─────────────────────────────────────────────

	def _add_order_card(self, order: dict):
		"""Crée et insère le bloc d'une commande avec ses sous-conteneurs de plats."""
		card = QFrame()
		card.setObjectName("commandeCard")
		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(8, 8, 8, 8)
		card_layout.setSpacing(6)

		card_layout.addWidget(self._build_card_header(order))

		visible_items = order.get("items", [])
		for item in visible_items:
			card_layout.addWidget(self._build_plat_subcard(item))

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

	def _build_card_header(self, order: dict) -> QFrame:
		"""Construit le bandeau d'en-tête avec l'ID de commande et le nombre de plats."""
		header = QFrame()
		header.setObjectName("commandeCardHeader")
		header_layout = QHBoxLayout(header)
		header_layout.setContentsMargins(0, 0, 0, 0)
		header_layout.setSpacing(8)

		order_id = order.get("id", "")
		id_label = QLabel(f"Commande {order_id}")
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
