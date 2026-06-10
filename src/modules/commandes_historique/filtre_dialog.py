#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filtre_dialog.py - Fenêtre de paramétrage des filtres de l'historique

Description:
    QDialog regroupant tous les paramètres de filtrage de la vue historique :
    statut de commande, statut de plat (avec gestion de compatibilité selon le
    statut commande), période (date + heure) et type de plat.
    Trois boutons en pied de fenêtre : appliquer, annuler, remise à zéro.

Author :
    Dracudar

Version:
    1.3

Date de création :
    2026.06.09

Date de modification:
    2026.06.10
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Optional, Set

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
	QDialog,
	QFrame,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QPushButton,
	QVBoxLayout,
	QWidget,
)


# ── Couleurs ──────────────────────────────────────────────────────────────────
_BG_DIALOG  = "#36393f"
_BG_SECTION = "#2f3136"
_BORDER     = "#60646c"
_TEXT_TITLE = "#f5f5f5"
_TEXT_LABEL = "#a8acb3"

# ── Options de filtre statut commande ────────────────────────────────────────
_FILTRES_STATUT: List[tuple] = [
	("Tout",     None),
	("En cours", "validée"),
	("Terminée", "terminée"),
	("Annulée",  "annulée"),
]

# ── Options de filtre statut plat ────────────────────────────────────────────
_FILTRES_STATUT_PLAT: List[tuple] = [
	("En prép.", "en préparation"),
	("Prêt",    "prêt"),
	("Livré",   "livré"),
	("Annulé",  "annulé"),
]

# Statuts commande compatibles avec chaque statut plat (None = tous)
_COMPAT_STATUT_PLAT: Dict[str, Optional[FrozenSet[str]]] = {
	"en préparation": frozenset({"validée"}),
	"prêt":           frozenset({"validée", "annulée"}),
	"livré":          None,
	"annulé":         None,
}


class StrikedFilterButton(QPushButton):
	"""Bouton filtre avec barre diagonale quand l'option est incompatible avec le contexte."""

	def __init__(self, text: str, parent=None):
		super().__init__(text, parent)
		self._striked = False

	def set_striked(self, striked: bool):
		if striked:
			self.setChecked(False)
		self._striked = striked
		self.update()

	@property
	def is_striked(self) -> bool:
		return self._striked

	def mousePressEvent(self, event):
		if self._striked:
			return
		super().mousePressEvent(event)

	def paintEvent(self, event):
		super().paintEvent(event)
		if self._striked:
			painter = QPainter(self)
			painter.setRenderHint(QPainter.RenderHint.Antialiasing)
			painter.setPen(QPen(QColor("#c0392b"), 1.5))
			r = self.rect()
			painter.drawLine(r.topLeft(), r.bottomRight())
			painter.end()


class FiltreHistoriqueDialog(QDialog):
	"""Fenêtre modale de paramétrage des filtres de l'historique des commandes."""

	def __init__(
		self,
		parent=None,
		current_filters: Optional[Dict[str, Any]] = None,
		available_plat_types: Optional[List[str]] = None,
	):
		super().__init__(parent)
		self.setWindowTitle("Filtres")
		self.setModal(True)
		self.setMinimumWidth(440)
		self._initial_filters: Dict[str, Any] = dict(current_filters or {})
		self._available_plat_types: List[str] = sorted(available_plat_types or [])
		self._status_btns: Dict[Optional[str], QPushButton] = {}
		self._plat_status_btns: Dict[str, QPushButton] = {}
		self._plat_btns: Dict[str, QPushButton] = {}
		self._priority_btn: Optional[QPushButton] = None
		self._build_ui()
		self._load_filters(self._initial_filters)

	# ── Construction de l'interface ─────────────────────────────────────────

	def _build_ui(self):
		root = QVBoxLayout(self)
		root.setContentsMargins(16, 16, 16, 16)
		root.setSpacing(12)

		root.addWidget(self._section_statut())
		root.addWidget(self._section_plat_statuts())
		root.addWidget(self._section_periode())
		if self._available_plat_types:
			root.addWidget(self._section_plat_types())
		root.addStretch()
		root.addWidget(self._build_footer())

		self.setStyleSheet(
			f"""
			QDialog {{
				background-color: {_BG_DIALOG};
			}}
			QFrame#section {{
				background-color: {_BG_SECTION};
				border: 1px solid {_BORDER};
				border-radius: 6px;
			}}
			QLabel#sectionTitle {{
				color: {_TEXT_TITLE};
				font-size: 13px;
				font-weight: 700;
			}}
			QLabel#fieldLabel {{
				color: {_TEXT_LABEL};
				font-size: 12px;
			}}
			QLineEdit {{
				background-color: #3b3f46;
				color: {_TEXT_TITLE};
				border: 1px solid #676d79;
				border-radius: 5px;
				padding: 5px 8px;
			}}
			QPushButton#filterBtn {{
				background-color: #3a3d43;
				border: 1px solid {_BORDER};
				border-radius: 12px;
				color: {_TEXT_LABEL};
				font-size: 12px;
				font-weight: 600;
				padding: 3px 14px;
				min-height: 26px;
			}}
			QPushButton#filterBtn:checked {{
				background-color: #4f545e;
				border: 1px solid #a8acb3;
				color: {_TEXT_TITLE};
			}}
			QPushButton#filterBtn:hover:!checked {{
				background-color: #4a4e55;
			}}
			QPushButton#filterBtnPriority {{
				background-color: #3a3d43;
				border: 1px solid {_BORDER};
				border-radius: 12px;
				color: #c0392b;
				font-size: 12px;
				font-weight: 700;
				padding: 3px 14px;
				min-height: 26px;
			}}
			QPushButton#filterBtnPriority:checked {{
				background-color: #5e1a1a;
				border: 1px solid #e74c3c;
				color: #f5f5f5;
			}}
			QPushButton#filterBtnPriority:hover:!checked {{
				background-color: #4a3535;
			}}
			QPushButton#applyBtn {{
				background-color: #2d6a4f;
				border: 1px solid #40916c;
				border-radius: 7px;
				color: {_TEXT_TITLE};
				font-size: 14px;
				font-weight: 700;
				min-height: 36px;
				padding: 6px 16px;
			}}
			QPushButton#applyBtn:hover {{
				background-color: #40916c;
			}}
			QPushButton#cancelBtn {{
				background-color: #4f545e;
				border: 1px solid #7d8390;
				border-radius: 7px;
				color: {_TEXT_TITLE};
				font-size: 14px;
				font-weight: 700;
				min-height: 36px;
				padding: 6px 16px;
			}}
			QPushButton#cancelBtn:hover {{
				background-color: #626978;
			}}
			QPushButton#resetBtn {{
				background-color: #5e1a1a;
				border: 1px solid #c0392b;
				border-radius: 7px;
				color: {_TEXT_TITLE};
				font-size: 14px;
				font-weight: 700;
				min-height: 36px;
				padding: 6px 16px;
			}}
			QPushButton#resetBtn:hover {{
				background-color: #c0392b;
			}}
			"""
		)

	def _make_section(self, title: str) -> tuple[QFrame, QVBoxLayout]:
		frame = QFrame()
		frame.setObjectName("section")
		layout = QVBoxLayout(frame)
		layout.setContentsMargins(12, 10, 12, 10)
		layout.setSpacing(8)
		lbl = QLabel(title)
		lbl.setObjectName("sectionTitle")
		layout.addWidget(lbl)
		return frame, layout

	def _make_field_label(self, text: str) -> QLabel:
		lbl = QLabel(text)
		lbl.setObjectName("fieldLabel")
		lbl.setFixedWidth(22)
		return lbl

	def _section_statut(self) -> QFrame:
		frame, layout = self._make_section("Statut de la commande")

		status_row = QHBoxLayout()
		status_row.setSpacing(6)
		for label, key in _FILTRES_STATUT:
			btn = QPushButton(label)
			btn.setCheckable(True)
			btn.setObjectName("filterBtn")
			btn.clicked.connect(lambda _, k=key: self._on_status_click(k))
			self._status_btns[key] = btn
			status_row.addWidget(btn)
		status_row.addStretch()
		layout.addLayout(status_row)

		priority_row = QHBoxLayout()
		priority_row.setSpacing(6)
		self._priority_btn = QPushButton("! Prioritaire")
		self._priority_btn.setCheckable(True)
		self._priority_btn.setObjectName("filterBtnPriority")
		priority_row.addWidget(self._priority_btn)
		priority_row.addStretch()
		layout.addLayout(priority_row)

		return frame

	def _section_plat_statuts(self) -> QFrame:
		frame, layout = self._make_section("Statut du plat")
		row = QHBoxLayout()
		row.setSpacing(6)
		for label, key in _FILTRES_STATUT_PLAT:
			btn = StrikedFilterButton(label)
			btn.setCheckable(True)
			btn.setObjectName("filterBtn")
			self._plat_status_btns[key] = btn
			row.addWidget(btn)
		row.addStretch()
		layout.addLayout(row)
		return frame

	def _section_periode(self) -> QFrame:
		frame, layout = self._make_section("Période")

		du_row = QHBoxLayout()
		du_row.setSpacing(6)
		du_row.addWidget(self._make_field_label("Du"))
		self.date_from = QLineEdit()
		self.date_from.setPlaceholderText("JJ/MM/AAAA")
		self.date_from.setMaximumWidth(115)
		du_row.addWidget(self.date_from)
		self.time_from = QLineEdit()
		self.time_from.setPlaceholderText("HH:MM")
		self.time_from.setMaximumWidth(68)
		du_row.addWidget(self.time_from)
		du_row.addStretch()
		layout.addLayout(du_row)

		au_row = QHBoxLayout()
		au_row.setSpacing(6)
		au_row.addWidget(self._make_field_label("Au"))
		self.date_to = QLineEdit()
		self.date_to.setPlaceholderText("JJ/MM/AAAA")
		self.date_to.setMaximumWidth(115)
		au_row.addWidget(self.date_to)
		self.time_to = QLineEdit()
		self.time_to.setPlaceholderText("HH:MM")
		self.time_to.setMaximumWidth(68)
		au_row.addWidget(self.time_to)
		au_row.addStretch()
		layout.addLayout(au_row)

		return frame

	def _section_plat_types(self) -> QFrame:
		frame, layout = self._make_section("Type de plat")
		row = QHBoxLayout()
		row.setSpacing(6)
		for plat_type in self._available_plat_types:
			btn = QPushButton(plat_type)
			btn.setCheckable(True)
			btn.setObjectName("filterBtn")
			self._plat_btns[plat_type] = btn
			row.addWidget(btn)
		row.addStretch()
		layout.addLayout(row)
		return frame

	def _build_footer(self) -> QWidget:
		footer = QWidget()
		layout = QHBoxLayout(footer)
		layout.setContentsMargins(0, 4, 0, 0)
		layout.setSpacing(8)

		apply_btn = QPushButton("Fermer et appliquer")
		apply_btn.setObjectName("applyBtn")
		apply_btn.clicked.connect(self.accept)

		cancel_btn = QPushButton("Annuler")
		cancel_btn.setObjectName("cancelBtn")
		cancel_btn.clicked.connect(self.reject)

		reset_btn = QPushButton("Raz Filtres")
		reset_btn.setObjectName("resetBtn")
		reset_btn.clicked.connect(self._reset_and_accept)

		layout.addWidget(apply_btn, 1)
		layout.addWidget(cancel_btn)
		layout.addWidget(reset_btn)
		return footer

	# ── Logique interne ─────────────────────────────────────────────────────

	def _on_status_click(self, key: Optional[str]):
		"""Maintient l'exclusivité des boutons de statut (un seul actif à la fois)."""
		for k, btn in self._status_btns.items():
			btn.setChecked(k == key)
		self._update_plat_status_availability(key)

	def _update_plat_status_availability(self, active_cmd_status: Optional[str]):
		"""Barre en diagonale les boutons statut plat incompatibles avec le statut commande."""
		for plat_status, btn in self._plat_status_btns.items():
			compat = _COMPAT_STATUT_PLAT.get(plat_status)
			compatible = (
				active_cmd_status is None
				or compat is None
				or active_cmd_status in compat
			)
			btn.set_striked(not compatible)

	def _load_filters(self, filters: Dict[str, Any]):
		"""Remplit tous les contrôles à partir d'un dict de filtres."""
		active_status = filters.get("status", None)
		for k, btn in self._status_btns.items():
			btn.setChecked(k == active_status)

		if self._priority_btn is not None:
			self._priority_btn.setChecked(bool(filters.get("priority_only", False)))

		self._update_plat_status_availability(active_status)

		active_plat_statuses: Set[str] = set(filters.get("plat_statuses") or set())
		for ps, btn in self._plat_status_btns.items():
			btn.setChecked(not btn.is_striked and ps in active_plat_statuses)

		self.date_from.setText(filters.get("date_from", ""))
		self.time_from.setText(filters.get("time_from", ""))
		self.date_to.setText(filters.get("date_to", ""))
		self.time_to.setText(filters.get("time_to", ""))

		active_types: Set[str] = set(filters.get("plat_types") or set())
		for pt, btn in self._plat_btns.items():
			btn.setChecked(pt in active_types)

	def _reset_and_accept(self):
		"""Remet tous les filtres à zéro puis ferme la fenêtre en acceptant."""
		self._load_filters({})
		self.accept()

	# ── API publique ─────────────────────────────────────────────────────────

	def get_filters(self) -> Dict[str, Any]:
		"""Retourne le dict de filtres correspondant à l'état actuel des contrôles."""
		active_status = next(
			(k for k, btn in self._status_btns.items() if btn.isChecked()),
			None,
		)
		active_plat_statuses: Set[str] = {
			ps for ps, btn in self._plat_status_btns.items() if btn.isChecked()
		}
		active_types: Set[str] = {pt for pt, btn in self._plat_btns.items() if btn.isChecked()}
		return {
			"status":        active_status,
			"priority_only": self._priority_btn.isChecked() if self._priority_btn is not None else False,
			"date_from":     self.date_from.text().strip(),
			"time_from":     self.time_from.text().strip(),
			"date_to":       self.date_to.text().strip(),
			"time_to":       self.time_to.text().strip(),
			"plat_types":    active_types,
			"plat_statuses": active_plat_statuses,
		}
