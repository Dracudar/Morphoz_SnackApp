from __future__ import annotations

from typing import Any, Dict, List

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

from src.UI.utils.data_sources import get_completed_orders


class CommandesHistoriqueModule(QFrame):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("historiqueModule")
		self._build_ui()
		self._build_timer()
		self.refresh_orders()

	def _build_ui(self):
		self.setFrameShape(QFrame.Shape.StyledPanel)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(14, 14, 14, 14)
		main_layout.setSpacing(10)

		title = QLabel("Historique")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setObjectName("sectionTitle")
		main_layout.addWidget(title)

		search_row = QHBoxLayout()
		self.search_field = QLineEdit()
		self.search_field.setPlaceholderText("Rechercher par ID, plat ou statut")
		self.search_field.textChanged.connect(self.refresh_orders)
		self.reload_button = QPushButton("Rafraichir")
		self.reload_button.clicked.connect(self.refresh_orders)
		search_row.addWidget(self.search_field, 1)
		search_row.addWidget(self.reload_button)
		main_layout.addLayout(search_row)

		self.summary_label = QLabel("Commandes validees : 0")
		self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.summary_label.setStyleSheet("color: #d6d6d6; font-size: 13px; font-weight: 600;")
		main_layout.addWidget(self.summary_label)

		self.scroll_area = QScrollArea()
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
		main_layout.addWidget(self.scroll_area, 1)

		self.list_container = QWidget()
		self.list_layout = QVBoxLayout(self.list_container)
		self.list_layout.setContentsMargins(0, 0, 0, 0)
		self.list_layout.setSpacing(8)
		self.list_layout.addStretch()
		self.scroll_area.setWidget(self.list_container)

		self.setStyleSheet(
			"""
			QFrame#historiqueModule {
				background-color: #2f3136;
				border: 1px solid #7f7f7f;
			}
			QLabel#sectionTitle {
				color: #f5f5f5;
				font-size: 22px;
				font-weight: 700;
				padding: 4px;
			}
			QLineEdit {
				background-color: #3b3f46;
				color: #f5f5f5;
				border: 1px solid #676d79;
				border-radius: 6px;
				padding: 6px 8px;
			}
			QPushButton {
				background-color: #4f545e;
				border: 1px solid #7d8390;
				border-radius: 7px;
				color: #f5f5f5;
				font-size: 14px;
				font-weight: 700;
				min-height: 34px;
				padding: 6px 12px;
			}
			QPushButton:hover {
				background-color: #626978;
			}
			"""
		)

	def _build_timer(self):
		self.refresh_timer = QTimer(self)
		self.refresh_timer.setInterval(5000)
		self.refresh_timer.timeout.connect(self.refresh_orders)
		self.refresh_timer.start()

	def clear_cards(self):
		while self.list_layout.count() > 1:
			item = self.list_layout.takeAt(0)
			widget = item.widget()
			if widget is not None:
				widget.deleteLater()

	def refresh_orders(self):
		orders = get_completed_orders()
		query = self.search_field.text().strip().lower()

		if query:
			orders = [order for order in orders if self._matches(order, query)]

		self.clear_cards()
		self.summary_label.setText(f"Commandes validees : {len(orders)}")

		if not orders:
			empty = QLabel("Aucune commande terminee trouvee.")
			empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
			empty.setStyleSheet("color: #d6d6d6; font-size: 14px;")
			self.list_layout.insertWidget(0, empty)
			return

		for order in orders:
			self._add_order_card(order)

	def _matches(self, order: Dict[str, Any], query: str) -> bool:
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

	def _add_order_card(self, order: Dict[str, Any]):
		card = QFrame()
		card.setFrameShape(QFrame.Shape.StyledPanel)
		card.setStyleSheet(
			"""
			QFrame {
				background-color: #3b3f46;
				border: 1px solid #60646c;
				border-radius: 7px;
			}
			"""
		)

		card_layout = QVBoxLayout(card)
		card_layout.setContentsMargins(8, 8, 8, 8)
		card_layout.setSpacing(6)

		header = QLabel(
			f"Commande {order.get('id', '')} | {order.get('status', '')} | Montant: {self._format_amount(order.get('amount'))}"
		)
		header.setStyleSheet("color: #f5f5f5; font-size: 13px; font-weight: 700;")
		card_layout.addWidget(header)

		dates = QLabel(
			f"Creation: {self._format_date(order.get('created_at'))} | Validation: {self._format_date(order.get('validation_at'))} | Livraison: {self._format_date(order.get('delivery_at'))}"
		)
		dates.setWordWrap(True)
		dates.setStyleSheet("color: #d6d6d6; font-size: 12px;")
		card_layout.addWidget(dates)

		items = QLabel(self._format_items(order.get("items", [])))
		items.setWordWrap(True)
		items.setStyleSheet("color: #d6d6d6; font-size: 12px;")
		card_layout.addWidget(items)

		self.list_layout.insertWidget(self.list_layout.count() - 1, card)

	def _format_amount(self, value: Any) -> str:
		if isinstance(value, (int, float)):
			return f"{value:.2f} €"
		return "-"

	def _format_date(self, value: Any) -> str:
		if isinstance(value, list) and len(value) >= 2:
			return f"{value[0]} {value[1]}".strip()
		if isinstance(value, str):
			return value
		return "-"

	def _format_items(self, items: List[Dict[str, Any]]) -> str:
		if not items:
			return "Aucun detail disponible."
		lines = []
		for item in items:
			label = item.get("nom") or item.get("plat") or item.get("id") or "Article"
			status = item.get("status", "")
			lines.append(f"- {label} [{status}]")
		return "\n".join(lines)
