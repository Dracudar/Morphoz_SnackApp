#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conteneur_suivi_commande.py - Widget suivi commandes

Description:
	Conteneur de suivi des commandes en préparation pour la colonne droite.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.18

Date de modification:
    2026.05.18
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
	QFrame,
	QHBoxLayout,
	QLabel,
	QPushButton,
	QScrollArea,
	QVBoxLayout,
	QWidget,
)

from src.UI.utils.data_sources import get_live_orders


class ConteneurSuiviCommande(QFrame):
	"""Affiche et rafraichit la liste des commandes en preparation."""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("suiviContainer")
		self._build_ui()
		self._build_timer()
		self.refresh_orders()

	def _build_ui(self):
		self.setFrameShape(QFrame.Shape.StyledPanel)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(10, 10, 10, 10)
		main_layout.setSpacing(8)

		self.title_label = QLabel("Commandes en preparation : 0")
		self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.title_label.setObjectName("suiviTitle")
		main_layout.addWidget(self.title_label)

		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
		main_layout.addWidget(self.scroll_area)

		self.list_container = QWidget()
		self.list_layout = QVBoxLayout(self.list_container)
		self.list_layout.setContentsMargins(0, 0, 0, 0)
		self.list_layout.setSpacing(6)
		self.list_layout.addStretch()
		self.scroll_area.setWidget(self.list_container)

		self.setStyleSheet(
			"""
			QFrame#suiviContainer {
				background-color: #2f3136;
				border: 1px solid #7f7f7f;
			}
			QLabel#suiviTitle {
				color: #f5f5f5;
				font-size: 17px;
				font-weight: 700;
				padding: 4px;
			}
			"""
		)

	def _build_timer(self):
		self.refresh_timer = QTimer(self)
		self.refresh_timer.setInterval(2000)
		self.refresh_timer.timeout.connect(self.refresh_orders)
		self.refresh_timer.start()

	def clear_orders(self):
		while self.list_layout.count() > 1:
			item = self.list_layout.takeAt(0)
			widget = item.widget()
			if widget is not None:
				widget.deleteLater()

	def refresh_orders(self):
		orders = get_live_orders()
		self.clear_orders()

		total_files = len(orders)
		total_plats = sum(order.get("active_count", 0) for order in orders)
		self.title_label.setText(
			f"Commandes en preparation : {total_files} | Plats actifs : {total_plats}"
		)

		for order in orders:
			self._add_order_card(order)

	def _add_order_card(self, order):
		card = QFrame()
		card.setFrameShape(QFrame.Shape.StyledPanel)
		card.setStyleSheet(
			"""
			QFrame {
				background-color: #3b3f46;
				border: 1px solid #60646c;
				border-radius: 6px;
			}
			"""
		)

		card_layout = QHBoxLayout(card)
		card_layout.setContentsMargins(6, 4, 6, 4)
		card_layout.setSpacing(8)

		ready_button = QPushButton("Pret")
		ready_button.setMinimumWidth(68)
		ready_button.setStyleSheet(
			"""
			QPushButton {
				background-color: #5b606b;
				color: #f5f5f5;
				border: 1px solid #818793;
				border-radius: 4px;
				padding: 4px 8px;
				font-weight: 600;
			}
			QPushButton:hover {
				background-color: #6d7481;
			}
			"""
		)
		card_layout.addWidget(ready_button)

		text_area = QVBoxLayout()
		text_area.setSpacing(2)

		order_title = QLabel(f"{order.get('id', '')}")
		order_title.setStyleSheet("color: #f5f5f5; font-size: 13px; font-weight: 700;")
		text_area.addWidget(order_title)

		summary = QLabel(self._build_order_summary(order))
		summary.setWordWrap(True)
		summary.setStyleSheet("color: #d6d6d6; font-size: 12px; font-weight: 500;")
		text_area.addWidget(summary)

		card_layout.addLayout(text_area, 1)
		self.list_layout.insertWidget(self.list_layout.count() - 1, card)

	def _build_order_summary(self, order):
		items = order.get("items", [])
		lines = []

		for item in items:
			status = item.get("status", "Inconnu")
			label = item.get("nom") or item.get("plat") or item.get("id")
			lines.append(f"{label} [{status}]")

		if not lines:
			lines.append("Aucun plat en cours")

		return "\n".join(lines)
