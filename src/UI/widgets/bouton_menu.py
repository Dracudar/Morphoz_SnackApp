#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bouton_menu.py - Widget bouton menu

Description:
	Définition d'un bouton de menu réutilisable pour la zone de saisie.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.05.18

Date de modification:
    2026.05.18
"""

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QPushButton


class BoutonMenu(QPushButton):
	"""Bouton stylisé pour les familles de plats et les modules."""

	def __init__(self, texte: str, icon_path: str | None = None, parent=None):
		super().__init__(texte, parent)
		self.setObjectName("menuButton")
		self.setMinimumSize(120, 90)

		if icon_path:
			self.setIcon(QIcon(icon_path))
			self.setIconSize(QSize(42, 42))

		self.setStyleSheet(
			"""
			QPushButton#menuButton {
				background-color: #45484f;
				border: 1px solid #6a6f79;
				border-radius: 8px;
				color: #f1f1f1;
				font-size: 14px;
				font-weight: 600;
				padding: 8px;
				text-align: center;
			}
			QPushButton#menuButton:hover {
				background-color: #555b66;
			}
			QPushButton#menuButton:pressed {
				background-color: #3a3e45;
			}
			QPushButton#menuButton:disabled {
				background-color: #3a3d43;
				border: 1px solid #595d64;
				color: #9aa0a8;
			}
			"""
		)
