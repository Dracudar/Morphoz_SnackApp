#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI.py

Description:
    Interface Qt/PySide6 du module carte : consultation et gestion de la carte des plats.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2025.05.29

Date de modification:
    2026.06.03
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QComboBox,
	QDoubleSpinBox,
	QFrame,
	QFormLayout,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMessageBox,
	QPushButton,
	QSplitter,
	QTextEdit,
	QTreeWidget,
	QTreeWidgetItem,
	QVBoxLayout,
	QWidget,
)

from src.backend.data.carte import get_card_data, save_card_data
from src.backend import logger


class CarteModule(QFrame):
	"""Module de gestion de la carte : consultation et édition des catégories et recettes."""

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("carteModule")
		self.card_data: Dict[str, Any] = {}
		self.current_selection: Optional[Dict[str, Any]] = None
		self._build_ui()
		self.reload_from_disk()

	def _build_ui(self):
		"""Construit l'interface : arbre de la carte à gauche, formulaire d'édition à droite."""
		self.setFrameShape(QFrame.Shape.StyledPanel)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(14, 14, 14, 14)
		main_layout.setSpacing(12)

		title = QLabel("Carte")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setObjectName("sectionTitle")
		main_layout.addWidget(title)

		splitter = QSplitter()

		self.tree = QTreeWidget()
		self.tree.setHeaderLabels(["Element", "Etat", "Prix"])
		self.tree.itemSelectionChanged.connect(self._sync_selection)
		splitter.addWidget(self.tree)

		editor = QWidget()
		editor_layout = QVBoxLayout(editor)
		editor_layout.setContentsMargins(0, 0, 0, 0)
		editor_layout.setSpacing(10)

		description = QLabel(
			"Selectionne une categorie ou une recette, puis modifie le nom, le prix, l'etat et les ingredients."
		)
		description.setWordWrap(True)
		description.setStyleSheet("color: #d6d6d6; font-size: 14px;")
		editor_layout.addWidget(description)

		form = QFormLayout()
		form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
		form.setHorizontalSpacing(12)
		form.setVerticalSpacing(10)

		self.category_field = QLineEdit()
		self.recipe_field = QLineEdit()
		self.price_field = QDoubleSpinBox()
		self.price_field.setRange(0.0, 999.99)
		self.price_field.setDecimals(2)
		self.state_field = QComboBox()
		self.state_field.setEditable(True)
		self.state_field.addItems(["Disponible", "Retiré", "Hors stock"])
		self.base_field = QTextEdit()
		self.ingredients_field = QTextEdit()

		form.addRow("Categorie", self.category_field)
		form.addRow("Recette", self.recipe_field)
		form.addRow("Prix", self.price_field)
		form.addRow("Etat", self.state_field)
		form.addRow("Base", self.base_field)
		form.addRow("Ingredients", self.ingredients_field)

		editor_layout.addLayout(form)

		buttons = QHBoxLayout()
		buttons.setSpacing(8)

		self.reload_button = QPushButton("Recharger")
		self.clear_button = QPushButton("Nouveau")
		self.save_button = QPushButton("Enregistrer")
		self.delete_button = QPushButton("Supprimer")

		self.reload_button.clicked.connect(self.reload_from_disk)
		self.clear_button.clicked.connect(self.clear_form)
		self.save_button.clicked.connect(self.save_entry)
		self.delete_button.clicked.connect(self.delete_entry)

		buttons.addWidget(self.reload_button)
		buttons.addWidget(self.clear_button)
		buttons.addWidget(self.save_button)
		buttons.addWidget(self.delete_button)
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
			QFrame#carteModule {
				background-color: #2f3136;
				border: 1px solid #7f7f7f;
			}
			QLabel#sectionTitle {
				color: #f5f5f5;
				font-size: 22px;
				font-weight: 700;
				padding: 4px;
			}
			QTreeWidget, QTextEdit, QLineEdit, QComboBox, QDoubleSpinBox {
				background-color: #3b3f46;
				color: #f5f5f5;
				border: 1px solid #676d79;
				border-radius: 6px;
			}
			QTreeWidget::item:selected {
				background-color: #556070;
			}
			QPushButton {
				background-color: #4f545e;
				border: 1px solid #7d8390;
				border-radius: 7px;
				color: #f5f5f5;
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
		"""Recharge la carte depuis le fichier JSON et réinitialise l'arbre et le formulaire."""
		self.card_data = get_card_data()
		self._populate_tree()
		self.clear_form()
		self.status_label.setText("Carte rechargee.")

	def _populate_tree(self):
		"""Remplit l'arbre Qt avec les catégories et leurs recettes."""
		self.tree.blockSignals(True)
		self.tree.clear()

		for category_name, payload in self.card_data.items():
			category_state = ""
			category_price = ""
			if isinstance(payload, dict):
				category_state = str(payload.get("Etat", ""))
				price_value = payload.get("Prix")
				if isinstance(price_value, (int, float)):
					category_price = f"{price_value:.2f}"

			category_item = QTreeWidgetItem([category_name, category_state, category_price])
			category_item.setData(0, Qt.ItemDataRole.UserRole, {"kind": "category", "category": category_name})
			self.tree.addTopLevelItem(category_item)

			recipes = payload.get("Recettes") if isinstance(payload, dict) else None
			if isinstance(recipes, dict):
				for recipe_name, recipe_payload in recipes.items():
					if not isinstance(recipe_payload, dict):
						recipe_payload = {}
					recipe_state = str(recipe_payload.get("Etat", ""))
					recipe_price = recipe_payload.get("Prix")
					recipe_price_text = f"{recipe_price:.2f}" if isinstance(recipe_price, (int, float)) else ""
					recipe_item = QTreeWidgetItem([recipe_name, recipe_state, recipe_price_text])
					recipe_item.setData(
						0,
						Qt.ItemDataRole.UserRole,
						{"kind": "recipe", "category": category_name, "recipe": recipe_name},
					)
					category_item.addChild(recipe_item)

		self.tree.expandAll()
		self.tree.blockSignals(False)

	def _sync_selection(self):
		"""Met à jour le formulaire d'édition selon l'élément sélectionné dans l'arbre."""
		items = self.tree.selectedItems()
		if not items:
			return

		item = items[0]
		selection = item.data(0, Qt.ItemDataRole.UserRole) or {}
		self.current_selection = selection

		category_name = selection.get("category", item.text(0))
		self.category_field.setText(category_name)
		self.recipe_field.setText(selection.get("recipe", ""))

		node_data = self._resolve_node_data(category_name, selection.get("recipe"))
		if isinstance(node_data, dict):
			price = node_data.get("Prix")
			self.price_field.setValue(float(price) if isinstance(price, (int, float)) else 0.0)
			self.state_field.setCurrentText(str(node_data.get("Etat", "Disponible")))
			self.base_field.setPlainText(self._join_list(node_data.get("Base", [])))
			self.ingredients_field.setPlainText(self._join_list(node_data.get("Ingrédients", [])))

	def _resolve_node_data(self, category_name: str, recipe_name: Optional[str]):
		"""Retourne les données brutes du nœud (catégorie ou recette) depuis card_data."""
		category = self.card_data.get(category_name, {})
		if recipe_name and isinstance(category, dict):
			recipes = category.get("Recettes", {})
			if isinstance(recipes, dict):
				return recipes.get(recipe_name, {})
		return category if isinstance(category, dict) else {}

	def clear_form(self):
		"""Vide tous les champs du formulaire et désélectionne l'arbre."""
		self.current_selection = None
		self.category_field.clear()
		self.recipe_field.clear()
		self.price_field.setValue(0.0)
		self.state_field.setCurrentText("Disponible")
		self.base_field.clear()
		self.ingredients_field.clear()
		self.tree.clearSelection()

	def save_entry(self):
		"""Enregistre la catégorie ou la recette en cours d'édition dans card_data et sur disque."""
		category_name = self.category_field.text().strip()
		recipe_name = self.recipe_field.text().strip()

		if not category_name:
			QMessageBox.warning(self, "Carte", "Le nom de la categorie est obligatoire.")
			return

		category = self.card_data.setdefault(category_name, {})
		if not isinstance(category, dict):
			category = {}
			self.card_data[category_name] = category

		state_value = self.state_field.currentText().strip() or "Disponible"
		price_value = round(self.price_field.value(), 2)

		if recipe_name:
			recipes = category.setdefault("Recettes", {})
			if not isinstance(recipes, dict):
				recipes = {}
				category["Recettes"] = recipes

			recipes[recipe_name] = {
				"Prix": price_value,
				"Etat": state_value,
				"Base": self._split_list(self.base_field.toPlainText()),
				"Ingrédients": self._split_list(self.ingredients_field.toPlainText()),
			}
			category["Etat"] = category.get("Etat", state_value)
			message = f"Recette {recipe_name} enregistree."
		else:
			category["Etat"] = state_value
			category["Prix"] = price_value
			message = f"Categorie {category_name} enregistree."

		if not save_card_data(self.card_data):
			QMessageBox.critical(self, "Carte", "Impossible d'enregistrer la carte.")
			return

		if recipe_name:
			logger.log(logger.MODIFICATION_CARTE_MANUELLE, {
				"action": "enregistrement_recette",
				"categorie": category_name,
				"recette": recipe_name,
				"prix": price_value,
				"etat": state_value,
			})
		else:
			logger.log(logger.MODIFICATION_CARTE_MANUELLE, {
				"action": "enregistrement_categorie",
				"categorie": category_name,
				"etat": state_value,
				"prix": price_value,
			})

		self.status_label.setText(message)
		self.reload_from_disk()

	def delete_entry(self):
		"""Supprime la catégorie ou la recette sélectionnée de card_data et du fichier JSON."""
		category_name = self.category_field.text().strip()
		recipe_name = self.recipe_field.text().strip()

		if not category_name:
			return

		if recipe_name:
			category = self.card_data.get(category_name)
			if not isinstance(category, dict):
				return
			recipes = category.get("Recettes")
			if isinstance(recipes, dict) and recipe_name in recipes:
				del recipes[recipe_name]
				if not recipes:
					category.pop("Recettes", None)
			else:
				return
			message = f"Recette {recipe_name} supprimee."
		else:
			if category_name in self.card_data:
				del self.card_data[category_name]
			else:
				return
			message = f"Categorie {category_name} supprimee."

		if not save_card_data(self.card_data):
			QMessageBox.critical(self, "Carte", "Impossible d'enregistrer la carte.")
			return

		if recipe_name:
			logger.log(logger.MODIFICATION_CARTE_MANUELLE, {
				"action": "suppression_recette",
				"categorie": category_name,
				"recette": recipe_name,
			})
		else:
			logger.log(logger.MODIFICATION_CARTE_MANUELLE, {
				"action": "suppression_categorie",
				"categorie": category_name,
			})

		self.status_label.setText(message)
		self.reload_from_disk()

	def _join_list(self, values: Any) -> str:
		"""Convertit une liste en chaîne CSV (séparateur « , »)."""
		if isinstance(values, list):
			return ", ".join(str(value) for value in values)
		return ""

	def _split_list(self, text: str) -> List[str]:
		"""Découpe une chaîne CSV en liste de valeurs nettoyées."""
		return [part.strip() for part in text.split(",") if part.strip()]
