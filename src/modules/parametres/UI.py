#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parametres.py

Description:
    Interface Qt/PySide6 de gestion des paramètres de l'application :
    dossier data, configuration imprimante et options d'impression.

Author :
    Dracudar

Version:
    2.0

Date de création :
    2025.05.29

Date de modification:
    2026.06.06
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
	QCheckBox,
	QFileDialog,
	QFrame,
	QFormLayout,
	QGroupBox,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMessageBox,
	QPushButton,
	QVBoxLayout,
)

from src.backend.app_config import (
	get_data_folder,
	get_default_config,
	get_printer_config,
	get_print_options,
	save_app_config,
)


class ParametresModule(QFrame):
	"""Module de configuration : dossier data, imprimante et options d'impression."""

	config_changed = Signal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("parametresModule")
		self._build_ui()
		self.load_config()

	def _build_ui(self):
		"""Construit l'interface en trois sections : Données, Imprimante, Impression."""
		self.setFrameShape(QFrame.Shape.StyledPanel)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(14, 14, 14, 14)
		main_layout.setSpacing(14)

		title = QLabel("Paramètres")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setObjectName("sectionTitle")
		main_layout.addWidget(title)

		# ── Section Données ───────────────────────────────────────────────────
		group_data = QGroupBox("Données")
		group_data.setObjectName("paramGroup")
		layout_data = QFormLayout(group_data)
		layout_data.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
		layout_data.setHorizontalSpacing(12)
		layout_data.setVerticalSpacing(10)

		self.data_folder_field = QLineEdit()
		layout_data.addRow("Dossier data", self._path_row(self.data_folder_field, self._browse_data_folder))

		info = QLabel(
			"Les fichiers stock.json, carte_active.json, carte_archive.json\n"
			"et le sous-dossier commandes/ sont automatiquement créés si absents."
		)
		info.setObjectName("paramInfo")
		layout_data.addRow(info)

		main_layout.addWidget(group_data)

		# ── Section Imprimante ────────────────────────────────────────────────
		group_printer = QGroupBox("Imprimante thermique")
		group_printer.setObjectName("paramGroup")
		layout_printer = QFormLayout(group_printer)
		layout_printer.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
		layout_printer.setHorizontalSpacing(12)
		layout_printer.setVerticalSpacing(10)

		self.vendor_id_field = QLineEdit()
		self.vendor_id_field.setPlaceholderText("ex. 0x04B8")
		self.product_id_field = QLineEdit()
		self.product_id_field.setPlaceholderText("ex. 0x0E15")
		self.interface_field = QLineEdit()
		self.interface_field.setValidator(QIntValidator(0, 9, self))
		self.interface_field.setMaximumWidth(60)
		self.interface_field.setPlaceholderText("0")
		self.modele_field = QLineEdit()
		self.modele_field.setPlaceholderText("ex. TM-T20II")

		layout_printer.addRow("Vendor ID", self.vendor_id_field)
		layout_printer.addRow("Product ID", self.product_id_field)
		layout_printer.addRow("Interface USB", self.interface_field)
		layout_printer.addRow("Modèle / Profil", self.modele_field)

		main_layout.addWidget(group_printer)

		# ── Section Impression ────────────────────────────────────────────────
		group_print = QGroupBox("Options d'impression")
		group_print.setObjectName("paramGroup")
		layout_print = QVBoxLayout(group_print)
		layout_print.setSpacing(8)

		self.ticket_client_check = QCheckBox("Imprimer le ticket client (récapitulatif)")
		self.ticket_cuisine_check = QCheckBox("Imprimer le ticket cuisine")

		layout_print.addWidget(self.ticket_client_check)
		layout_print.addWidget(self.ticket_cuisine_check)

		main_layout.addWidget(group_print)

		# ── Boutons d'action ──────────────────────────────────────────────────
		buttons_layout = QHBoxLayout()
		buttons_layout.setSpacing(10)

		self.reload_button = QPushButton("Recharger")
		self.default_button = QPushButton("Valeurs par défaut")
		self.save_button = QPushButton("Enregistrer")

		self.reload_button.clicked.connect(self.load_config)
		self.default_button.clicked.connect(self.reset_defaults)
		self.save_button.clicked.connect(self.save_config)

		buttons_layout.addWidget(self.reload_button)
		buttons_layout.addWidget(self.default_button)
		buttons_layout.addWidget(self.save_button)
		main_layout.addLayout(buttons_layout)

		self.status_label = QLabel("")
		self.status_label.setWordWrap(True)
		self.status_label.setObjectName("paramStatus")
		main_layout.addWidget(self.status_label)

		main_layout.addStretch()

		self.setStyleSheet(
			"""
			QFrame#parametresModule {
				background-color: #2f3136;
				border: 1px solid #7f7f7f;
			}
			QLabel#sectionTitle {
				color: #f5f5f5;
				font-size: 22px;
				font-weight: 700;
				padding: 4px;
			}
			QGroupBox#paramGroup {
				color: #d6d6d6;
				font-size: 15px;
				font-weight: 600;
				border: 1px solid #555a64;
				border-radius: 7px;
				margin-top: 8px;
				padding: 10px 8px 8px 8px;
			}
			QGroupBox#paramGroup::title {
				subcontrol-origin: margin;
				subcontrol-position: top left;
				padding: 0 6px;
				left: 10px;
			}
			QLabel#paramInfo {
				color: #9da5b4;
				font-size: 12px;
			}
			QLabel#paramStatus {
				color: #a8d08d;
				font-size: 13px;
			}
			QLineEdit {
				background-color: #3b3f46;
				color: #f5f5f5;
				border: 1px solid #676d79;
				border-radius: 6px;
				padding: 6px 8px;
			}
			QCheckBox {
				color: #f5f5f5;
				font-size: 14px;
				spacing: 8px;
			}
			QCheckBox::indicator {
				width: 16px;
				height: 16px;
				border-radius: 3px;
				border: 1px solid #676d79;
				background-color: #3b3f46;
			}
			QCheckBox::indicator:checked {
				background-color: #5865f2;
				border-color: #5865f2;
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

	def _path_row(self, field: QLineEdit, callback):
		"""Crée une ligne composée d'un champ texte et d'un bouton Parcourir."""
		row = QHBoxLayout()
		row.setSpacing(8)
		row.addWidget(field, 1)
		button = QPushButton("Parcourir")
		button.clicked.connect(callback)
		row.addWidget(button)

		container = QFrame()
		container.setLayout(row)
		return container

	def _browse_data_folder(self):
		"""Ouvre un sélecteur de dossier pour le dossier data."""
		path = QFileDialog.getExistingDirectory(self, "Choisir le dossier data", self.data_folder_field.text())
		if path:
			self.data_folder_field.setText(path)

	def load_config(self):
		"""Charge la configuration actuelle et remplit tous les champs."""
		self.data_folder_field.setText(str(get_data_folder()))

		printer = get_printer_config()
		self.vendor_id_field.setText(f"0x{printer['vendor_id']:04X}")
		self.product_id_field.setText(f"0x{printer['product_id']:04X}")
		self.interface_field.setText(str(printer["interface"]))
		self.modele_field.setText(printer["modele"])

		options = get_print_options()
		self.ticket_client_check.setChecked(options["ticket_client"])
		self.ticket_cuisine_check.setChecked(options["ticket_cuisine"])

		self.status_label.setText("Configuration chargée.")

	def reset_defaults(self):
		"""Restaure les valeurs par défaut dans les champs sans sauvegarder."""
		defaults = get_default_config()

		self.data_folder_field.setText(defaults["data_folder"])

		printer = defaults["imprimante"]
		self.vendor_id_field.setText(printer["vendor_id"])
		self.product_id_field.setText(printer["product_id"])
		self.interface_field.setText(str(printer["interface"]))
		self.modele_field.setText(printer["modele"])

		self.ticket_client_check.setChecked(defaults["impression"]["ticket_client"])
		self.ticket_cuisine_check.setChecked(defaults["impression"]["ticket_cuisine"])

		self.status_label.setText("Valeurs par défaut restaurées.")

	def save_config(self):
		"""Valide les champs, crée la structure de fichiers et sauvegarde la configuration."""
		data_folder = self.data_folder_field.text().strip()
		vendor_id = self.vendor_id_field.text().strip()
		product_id = self.product_id_field.text().strip()
		interface = int(self.interface_field.text() or "0")
		modele = self.modele_field.text().strip()

		if not modele:
			QMessageBox.warning(self, "Paramètres", "Le modèle de l'imprimante doit être renseigné.")
			return

		# Validation basique du format hex pour vendor/product ID
		for label, value in [("Vendor ID", vendor_id), ("Product ID", product_id)]:
			try:
				int(value, 16) if value.startswith(("0x", "0X")) else int(value)
			except ValueError:
				QMessageBox.warning(self, "Paramètres", f"{label} invalide : '{value}'.\nFormat attendu : 0x04B8 ou 1208.")
				return

		ok = save_app_config(
			data_folder=data_folder,
			vendor_id=vendor_id,
			product_id=product_id,
			interface=interface,
			modele=modele,
			ticket_client=self.ticket_client_check.isChecked(),
			ticket_cuisine=self.ticket_cuisine_check.isChecked(),
		)

		if not ok:
			QMessageBox.critical(self, "Paramètres", "Impossible d'enregistrer la configuration ou de créer le dossier data.")
			return

		self.status_label.setText("Configuration enregistrée. Structure de fichiers vérifiée.")
		self.config_changed.emit()
