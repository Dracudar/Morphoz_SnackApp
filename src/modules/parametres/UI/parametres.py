from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
	QFileDialog,
	QFrame,
	QFormLayout,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMessageBox,
	QPushButton,
	QVBoxLayout,
)

from src.backend.app_config import get_app_paths, get_default_app_paths, save_app_paths


class ParametresModule(QFrame):
	config_changed = Signal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.setObjectName("parametresModule")
		self._build_ui()
		self.load_config()

	def _build_ui(self):
		self.setFrameShape(QFrame.Shape.StyledPanel)

		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(14, 14, 14, 14)
		main_layout.setSpacing(12)

		title = QLabel("Parametres")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setObjectName("sectionTitle")
		main_layout.addWidget(title)

		description = QLabel(
			"Selection des fichiers de travail utilises par l'application. "
			"Le bouton enregistrer met a jour la configuration sans fermer l'application."
		)
		description.setWordWrap(True)
		description.setStyleSheet("color: #d6d6d6; font-size: 14px;")
		main_layout.addWidget(description)

		form = QFormLayout()
		form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
		form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
		form.setHorizontalSpacing(12)
		form.setVerticalSpacing(10)

		self.stock_field = QLineEdit()
		self.menu_field = QLineEdit()
		self.archive_field = QLineEdit()

		form.addRow("Fichier stock", self._path_row(self.stock_field, self._browse_stock))
		form.addRow("Fichier carte", self._path_row(self.menu_field, self._browse_menu))
		form.addRow("Dossier archive", self._path_row(self.archive_field, self._browse_archive))

		main_layout.addLayout(form)

		buttons_layout = QHBoxLayout()
		buttons_layout.setSpacing(10)

		self.reload_button = QPushButton("Recharger")
		self.default_button = QPushButton("Valeurs par defaut")
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
		self.status_label.setStyleSheet("color: #a8d08d; font-size: 13px;")
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
				min-height: 38px;
				padding: 6px 12px;
			}
			QPushButton:hover {
				background-color: #626978;
			}
			"""
		)

	def _path_row(self, field: QLineEdit, callback):
		row = QHBoxLayout()
		row.setSpacing(8)
		row.addWidget(field, 1)
		button = QPushButton("Parcourir")
		button.clicked.connect(callback)
		row.addWidget(button)

		container = QFrame()
		container.setLayout(row)
		return container

	def _browse_stock(self):
		path, _ = QFileDialog.getOpenFileName(self, "Choisir le fichier stock", self.stock_field.text(), "JSON (*.json)")
		if path:
			self.stock_field.setText(path)

	def _browse_menu(self):
		path, _ = QFileDialog.getOpenFileName(self, "Choisir le fichier carte", self.menu_field.text(), "JSON (*.json)")
		if path:
			self.menu_field.setText(path)

	def _browse_archive(self):
		path = QFileDialog.getExistingDirectory(self, "Choisir le dossier archive", self.archive_field.text())
		if path:
			self.archive_field.setText(path)

	def load_config(self):
		paths = get_app_paths()
		self.stock_field.setText(paths["stock_file"])
		self.menu_field.setText(paths["menu_file"])
		self.archive_field.setText(paths["archive_folder"])
		self.status_label.setText("Configuration chargee.")

	def reset_defaults(self):
		paths = get_default_app_paths()
		self.stock_field.setText(paths["stock_file"])
		self.menu_field.setText(paths["menu_file"])
		self.archive_field.setText(paths["archive_folder"])
		self.status_label.setText("Valeurs par defaut restaurees.")

	def save_config(self):
		stock_path = self.stock_field.text().strip()
		menu_path = self.menu_field.text().strip()
		archive_path = self.archive_field.text().strip()

		if not stock_path or not menu_path or not archive_path:
			QMessageBox.warning(self, "Parametres", "Tous les chemins doivent etre renseignes.")
			return

		if not save_app_paths(stock_path, menu_path, archive_path):
			QMessageBox.critical(self, "Parametres", "Impossible d'enregistrer la configuration.")
			return

		self.status_label.setText("Configuration enregistree.")
		self.config_changed.emit()
