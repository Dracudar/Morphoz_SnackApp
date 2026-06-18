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
    2.7

Date de création :
    2025.05.29

Date de modification:
    2026.06.15
"""

from __future__ import annotations

from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QIntValidator
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

from pathlib import Path

from src.backend.app_config import (
	get_assets_path,
	get_data_folder,
	get_print_options,
	get_printer_config,
	save_app_config,
)
from src.backend import logger


class ParametresModule(QFrame):
	"""Module de configuration : dossier data, imprimante et options d'impression."""

	config_changed = Signal()
	go_back = Signal()
	go_to_poste_prep = Signal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("parametresModule")
		self._build_ui()
		self.load_config()

	def _build_ui(self):
		"""Construit l'interface : section Données puis section Impression unifiée."""
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
		layout_data = QVBoxLayout(group_data)
		layout_data.setSpacing(8)

		self.data_folder_field = QLineEdit()
		layout_data.addWidget(self._path_row(self.data_folder_field, self._browse_data_folder))

		info = QLabel(
			"Les fichiers stock.json, carte_active.json, carte_archive.json "
			"et le sous-dossier commandes/ sont automatiquement créés si absents."
		)
		info.setObjectName("paramInfo")
		info.setWordWrap(False)
		layout_data.addWidget(info)

		main_layout.addWidget(group_data)

		# ── Section Impression ────────────────────────────────────────────────
		group_impression = QGroupBox("Impression")
		group_impression.setObjectName("paramGroup")
		layout_impression = QVBoxLayout(group_impression)
		layout_impression.setSpacing(10)

		# Bouton bascule ON/OFF
		self.impression_toggle = QPushButton("● Activée")
		self.impression_toggle.setObjectName("impressionToggle")
		self.impression_toggle.setCheckable(True)
		self.impression_toggle.setChecked(True)
		self.impression_toggle.toggled.connect(self._toggle_impression)
		layout_impression.addWidget(self.impression_toggle)

		# Sous-blocs côte à côte : Identification (gauche) + Options (droite)
		sub_layout = QHBoxLayout()
		sub_layout.setSpacing(10)
		sub_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

		# ── Sous-bloc Identification ──────────────────────────────────────────
		self._group_identification = QGroupBox("Identification")
		self._group_identification.setObjectName("paramSubGroup")
		layout_ident = QFormLayout(self._group_identification)
		layout_ident.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
		layout_ident.setHorizontalSpacing(12)
		layout_ident.setVerticalSpacing(10)

		self.vendor_id_field = QLineEdit()
		self.vendor_id_field.setPlaceholderText("ex. 0x04B8")
		self.product_id_field = QLineEdit()
		self.product_id_field.setPlaceholderText("ex. 0x0E15")
		self.interface_field = QLineEdit()
		self.interface_field.setValidator(QIntValidator(0, 9, self))
		self.interface_field.setPlaceholderText("0")
		self.modele_field = QLineEdit()
		self.modele_field.setPlaceholderText("ex. TM-T20II")

		layout_ident.addRow("Vendor ID", self.vendor_id_field)
		layout_ident.addRow("Product ID", self.product_id_field)
		layout_ident.addRow("Interface USB", self.interface_field)
		layout_ident.addRow("Modèle / Profil", self.modele_field)

		# ── Sous-bloc Options ─────────────────────────────────────────────────
		self._group_options = QGroupBox("Impression auto à la validation")
		self._group_options.setObjectName("paramSubGroup")
		layout_opts = QVBoxLayout(self._group_options)
		layout_opts.setSpacing(10)

		self.ticket_client_check = QCheckBox("Ticket récap (client)")
		self.ticket_cuisine_check = QCheckBox("Ticket cuisine")
		layout_opts.addWidget(self.ticket_client_check)
		layout_opts.addWidget(self.ticket_cuisine_check)
		layout_opts.addStretch()

		sub_layout.addWidget(self._group_identification, 3)
		sub_layout.addWidget(self._group_options, 2)
		layout_impression.addLayout(sub_layout)

		main_layout.addWidget(group_impression)

		# ── Boutons d'action ──────────────────────────────────────────────────
		buttons_layout = QHBoxLayout()
		buttons_layout.setSpacing(10)

		self.back_button = QPushButton("  Retour")
		self.back_button.setObjectName("backButton")
		self.back_button.setIcon(QIcon(get_assets_path("icons", "return.svg")))
		self.back_button.setIconSize(QSize(18, 18))
		self.back_button.clicked.connect(self.go_back.emit)

		self.save_button = QPushButton("  Enregistrer")
		self.save_button.setIcon(QIcon(get_assets_path("icons", "save.svg")))
		self.save_button.setIconSize(QSize(18, 18))
		self.save_button.clicked.connect(self.save_config)

		buttons_layout.addWidget(self.back_button)
		buttons_layout.addStretch()
		buttons_layout.addWidget(self.save_button)

		self.status_label = QLabel("")
		self.status_label.setWordWrap(True)
		self.status_label.setObjectName("paramStatus")

		main_layout.addStretch()
		main_layout.addWidget(self.status_label)
		main_layout.addLayout(buttons_layout)

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
			QGroupBox#paramSubGroup {
				color: #c8c8c8;
				font-size: 13px;
				font-weight: 600;
				border: 1px solid #454a52;
				border-radius: 5px;
				margin-top: 6px;
				padding: 8px 6px 6px 6px;
			}
			QGroupBox#paramSubGroup::title {
				subcontrol-origin: margin;
				subcontrol-position: top left;
				padding: 0 4px;
				left: 8px;
			}
			QGroupBox#paramSubGroup:disabled {
				color: #555a64;
				border-color: #3a3d42;
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
			QLineEdit:disabled {
				background-color: #2a2d33;
				color: #555;
				border-color: #3a3d42;
			}
			QCheckBox {
				color: #f5f5f5;
				font-size: 14px;
				spacing: 8px;
			}
			QCheckBox:disabled {
				color: #666;
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
			QCheckBox::indicator:disabled {
				background-color: #2a2d33;
				border-color: #3a3d42;
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
			QPushButton#parcourirButton {
				min-height: 0;
				padding: 6px 10px;
				font-weight: 400;
			}
			QPushButton#impressionToggle {
				background-color: #2d5a27;
				border-color: #4a8a42;
				color: #c8efc2;
				font-size: 14px;
				font-weight: 600;
			}
			QPushButton#impressionToggle:hover {
				background-color: #3a7033;
			}
			QPushButton#impressionToggle:!checked {
				background-color: #5a2727;
				border-color: #8a4242;
				color: #efc2c2;
			}
			QPushButton#impressionToggle:!checked:hover {
				background-color: #703333;
			}
			"""
		)

	def _path_row(self, field: QLineEdit, callback):
		"""Crée une ligne composée d'un champ texte et d'un bouton Parcourir de même hauteur."""
		row = QHBoxLayout()
		row.setSpacing(8)
		row.addWidget(field, 1)
		button = QPushButton("Parcourir")
		button.setObjectName("parcourirButton")
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

	def _toggle_impression(self, active: bool):
		"""Active ou désactive les sous-sections imprimante selon l'état du bouton bascule."""
		self._group_identification.setEnabled(active)
		self._group_options.setEnabled(active)
		self.impression_toggle.setText("● Activée" if active else "○ Désactivée")

	def load_config(self):
		"""Charge la configuration actuelle et remplit tous les champs."""
		self.data_folder_field.setText(str(get_data_folder()))

		printer = get_printer_config()
		self.vendor_id_field.setText(f"0x{printer['vendor_id']:04X}")
		self.product_id_field.setText(f"0x{printer['product_id']:04X}")
		self.interface_field.setText(str(printer["interface"]))
		self.modele_field.setText(printer["modele"])

		options = get_print_options()
		self.impression_toggle.setChecked(options["impression_active"])
		self._toggle_impression(options["impression_active"])
		self.ticket_client_check.setChecked(options["ticket_client"])
		self.ticket_cuisine_check.setChecked(options["ticket_cuisine"])

		self.status_label.setText("Configuration chargée.")

	def save_config(self):
		"""Valide les champs, crée la structure de fichiers et sauvegarde la configuration."""
		data_folder = self.data_folder_field.text().strip()
		impression_active = self.impression_toggle.isChecked()
		vendor_id = self.vendor_id_field.text().strip()
		product_id = self.product_id_field.text().strip()
		interface = int(self.interface_field.text() or "0")
		modele = self.modele_field.text().strip()

		if impression_active and not modele:
			QMessageBox.warning(self, "Paramètres", "Le modèle de l'imprimante doit être renseigné.")
			return

		if impression_active:
			for label, value in [("Vendor ID", vendor_id), ("Product ID", product_id)]:
				try:
					int(value, 16) if value.startswith(("0x", "0X")) else int(value)
				except ValueError:
					QMessageBox.warning(self, "Paramètres", f"{label} invalide : '{value}'.\nFormat attendu : 0x04B8 ou 1208.")
					return

		# Capture de la config actuelle avant sauvegarde pour comparaison
		ancien_dossier = str(get_data_folder())
		ancienne_imprimante = get_printer_config()
		anciennes_options = get_print_options()

		ticket_client = self.ticket_client_check.isChecked()
		ticket_cuisine = self.ticket_cuisine_check.isChecked()

		# Log du changement de dossier AVANT la sauvegarde : ainsi il reste dans l'ancien journal
		# (après save_app_config, get_logs_folder_path() pointe déjà vers le nouveau dossier)
		nouveau_dossier = data_folder or ancien_dossier
		if Path(nouveau_dossier).resolve() != Path(ancien_dossier).resolve():
			logger.log(logger.MODIFICATION_DOSSIER_DONNEES, {
				"avant": str(Path(ancien_dossier)),
				"apres": str(Path(nouveau_dossier)),
			})

		ok = save_app_config(
			data_folder=data_folder,
			vendor_id=vendor_id,
			product_id=product_id,
			interface=interface,
			modele=modele,
			impression_active=impression_active,
			ticket_client=self.ticket_client_check.isChecked(),
			ticket_cuisine=self.ticket_cuisine_check.isChecked(),
		)

		if not ok:
			QMessageBox.critical(self, "Paramètres", "Impossible d'enregistrer la configuration ou de créer le dossier data.")
			return

		# Migration du journal du jour vers le nouveau dossier si le chemin a changé
		if Path(nouveau_dossier).resolve() != Path(ancien_dossier).resolve():
			logger.migrer_log_journalier(
				Path(ancien_dossier) / "logs",
				Path(nouveau_dossier) / "logs",
			)

		if impression_active != anciennes_options["impression_active"]:
			logger.log(logger.MODIFICATION_OPTIONS_IMPRESSION, {
				"avant": {"impression_active": anciennes_options["impression_active"]},
				"apres": {"impression_active": impression_active},
			})

		ancien_vendor = f"0x{ancienne_imprimante['vendor_id']:04X}"
		ancien_product = f"0x{ancienne_imprimante['product_id']:04X}"
		id_change = (
			vendor_id.lower() != ancien_vendor.lower() or
			product_id.lower() != ancien_product.lower() or
			interface != ancienne_imprimante["interface"] or
			modele != ancienne_imprimante["modele"]
		)
		activating = (not anciennes_options["impression_active"]) and impression_active

		if impression_active:
			if activating and not id_change:
				# Activation sans changement de paramètres : noter simplement les IDs en place
				logger.log(logger.MODIFICATION_PARAMETRES_IMPRIMANTE, {
					"apres": {"vendor_id": vendor_id, "product_id": product_id,
							  "interface": interface, "modele": modele},
				})
			elif id_change:
				# Modification des valeurs (avec ou sans activation simultanée)
				logger.log(logger.MODIFICATION_PARAMETRES_IMPRIMANTE, {
					"avant": {"vendor_id": ancien_vendor, "product_id": ancien_product,
							  "interface": ancienne_imprimante["interface"], "modele": ancienne_imprimante["modele"]},
					"apres": {"vendor_id": vendor_id, "product_id": product_id,
							  "interface": interface, "modele": modele},
				})

		avant_tickets = {}
		apres_tickets = {}
		if ticket_client != anciennes_options["ticket_client"]:
			avant_tickets["ticket_client"] = anciennes_options["ticket_client"]
			apres_tickets["ticket_client"] = ticket_client
		if ticket_cuisine != anciennes_options["ticket_cuisine"]:
			avant_tickets["ticket_cuisine"] = anciennes_options["ticket_cuisine"]
			apres_tickets["ticket_cuisine"] = ticket_cuisine
		if avant_tickets:
			logger.log(logger.MODIFICATION_OPTIONS_IMPRESSION, {
				"avant": avant_tickets,
				"apres": apres_tickets,
			})

		self.status_label.setText("Configuration enregistrée. Structure de fichiers vérifiée.")
		self.config_changed.emit()
