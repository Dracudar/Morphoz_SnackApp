from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QCheckBox,
	QFrame,
	QFormLayout,
	QHBoxLayout,
	QLabel,
	QMessageBox,
	QPushButton,
	QSpinBox,
	QSplitter,
	QTreeWidget,
	QTreeWidgetItem,
	QVBoxLayout,
	QWidget,
)

from src.UI.utils.data_sources import get_stock_data, save_stock_data


class StockModule(QFrame):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("stockModule")
		self.stock_data: Dict[str, Any] = {}
		self.current_path: List[str] = []
		self._build_ui()
		self.reload_from_disk()

	def _build_ui(self):
		self.setFrameShape(QFrame.Shape.StyledPanel)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(14, 14, 14, 14)
		main_layout.setSpacing(12)

		title = QLabel("Stock")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setObjectName("sectionTitle")
		main_layout.addWidget(title)

		splitter = QSplitter()
		self.tree = QTreeWidget()
		self.tree.setHeaderLabels(["Element", "Quantite", "Etat"])
		self.tree.itemSelectionChanged.connect(self._sync_selection)
		splitter.addWidget(self.tree)

		editor = QWidget()
		editor_layout = QVBoxLayout(editor)
		editor_layout.setContentsMargins(0, 0, 0, 0)
		editor_layout.setSpacing(10)

		help_text = QLabel(
			"Selectionne un element du stock, modifie la quantite et l'etat, puis enregistre sans quitter l'application."
		)
		help_text.setWordWrap(True)
		help_text.setStyleSheet("color: #d6d6d6; font-size: 14px;")
		editor_layout.addWidget(help_text)

		form = QFormLayout()
		form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
		form.setHorizontalSpacing(12)
		form.setVerticalSpacing(10)

		self.path_label = QLabel("Aucun element selectionne")
		self.quantity_field = QSpinBox()
		self.quantity_field.setRange(0, 999999)
		self.out_of_stock_field = QCheckBox("Article indisponible")

		form.addRow("Chemin", self.path_label)
		form.addRow("Quantite", self.quantity_field)
		form.addRow("Etat", self.out_of_stock_field)
		editor_layout.addLayout(form)

		buttons = QHBoxLayout()
		buttons.setSpacing(8)

		self.reload_button = QPushButton("Recharger")
		self.save_button = QPushButton("Enregistrer")
		self.reload_button.clicked.connect(self.reload_from_disk)
		self.save_button.clicked.connect(self.save_entry)

		buttons.addWidget(self.reload_button)
		buttons.addWidget(self.save_button)
		editor_layout.addLayout(buttons)

		self.status_label = QLabel("")
		self.status_label.setWordWrap(True)
		self.status_label.setStyleSheet("color: #a8d08d; font-size: 13px;")
		editor_layout.addWidget(self.status_label)
		editor_layout.addStretch()

		splitter.addWidget(editor)
		splitter.setStretchFactor(0, 1)
		splitter.setStretchFactor(1, 2)
		main_layout.addWidget(splitter, 1)

		self.setStyleSheet(
			"""
			QFrame#stockModule {
				background-color: #2f3136;
				border: 1px solid #7f7f7f;
			}
			QLabel#sectionTitle {
				color: #f5f5f5;
				font-size: 22px;
				font-weight: 700;
				padding: 4px;
			}
			QTreeWidget, QLabel, QSpinBox, QPushButton {
				color: #f5f5f5;
			}
			QTreeWidget, QSpinBox {
				background-color: #3b3f46;
				border: 1px solid #676d79;
				border-radius: 6px;
			}
			QPushButton {
				background-color: #4f545e;
				border: 1px solid #7d8390;
				border-radius: 7px;
				font-size: 14px;
				font-weight: 700;
				min-height: 38px;
				padding: 6px 12px;
			}
			QPushButton:hover {
				background-color: #626978;
			}
			"""
		)

	def reload_from_disk(self):
		self.stock_data = get_stock_data()
		self._populate_tree()
		self.clear_form()
		self.status_label.setText("Stock recharge.")

	def _populate_tree(self):
		self.tree.blockSignals(True)
		self.tree.clear()
		self._add_branch([], self.stock_data, self.tree.invisibleRootItem())
		self.tree.expandAll()
		self.tree.blockSignals(False)

	def _add_branch(self, path: List[str], node: Any, parent_item):
		if not isinstance(node, dict):
			return

		for key, value in node.items():
			if isinstance(value, dict) and self._is_stock_leaf(value):
				quantity = value.get("Quantité", "")
				state_text = "HS" if value.get("OutOfStock", False) else "OK"
				item = QTreeWidgetItem([key, str(quantity), state_text])
				item.setData(0, Qt.ItemDataRole.UserRole, {"path": path + [key], "leaf": True})
				parent_item.addChild(item)
			elif isinstance(value, dict):
				item = QTreeWidgetItem([key, "", ""])
				item.setData(0, Qt.ItemDataRole.UserRole, {"path": path + [key], "leaf": False})
				parent_item.addChild(item)
				self._add_branch(path + [key], value, item)

	def _is_stock_leaf(self, node: Dict[str, Any]) -> bool:
		return any(key in node for key in ("Quantité", "OutOfStock", "Valeur")) and not any(
			isinstance(value, dict) and not self._is_stock_leaf(value)
			for value in node.values()
		)

	def _sync_selection(self):
		items = self.tree.selectedItems()
		if not items:
			return

		item = items[0]
		meta = item.data(0, Qt.ItemDataRole.UserRole) or {}
		path = meta.get("path", [])
		self.current_path = path
		self.path_label.setText(" / ".join(path) if path else "Aucun element selectionne")

		node = self._resolve_path(path)
		if isinstance(node, dict):
			self.quantity_field.setValue(int(node.get("Quantité", 0) or 0))
			self.out_of_stock_field.setChecked(bool(node.get("OutOfStock", False)))

	def _resolve_path(self, path: List[str]):
		node: Any = self.stock_data
		for key in path:
			if not isinstance(node, dict):
				return None
			node = node.get(key)
		return node

	def clear_form(self):
		self.current_path = []
		self.path_label.setText("Aucun element selectionne")
		self.quantity_field.setValue(0)
		self.out_of_stock_field.setChecked(False)
		self.tree.clearSelection()

	def save_entry(self):
		if not self.current_path:
			QMessageBox.warning(self, "Stock", "Selectionne un element du stock a modifier.")
			return

		parent_node = self.stock_data
		for key in self.current_path[:-1]:
			parent_node = parent_node.setdefault(key, {})
			if not isinstance(parent_node, dict):
				QMessageBox.warning(self, "Stock", "Chemin de stock invalide.")
				return

		leaf_key = self.current_path[-1]
		leaf_node = parent_node.get(leaf_key, {})
		if not isinstance(leaf_node, dict):
			leaf_node = {}

		leaf_node["Quantité"] = int(self.quantity_field.value())
		leaf_node["OutOfStock"] = self.out_of_stock_field.isChecked()
		parent_node[leaf_key] = leaf_node

		if not save_stock_data(self.stock_data):
			QMessageBox.critical(self, "Stock", "Impossible d'enregistrer le stock.")
			return

		self.status_label.setText("Stock enregistre.")
		self.reload_from_disk()
