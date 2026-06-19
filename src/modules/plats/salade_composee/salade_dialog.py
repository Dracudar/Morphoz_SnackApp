#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
salade_dialog.py

Description:
    Dialogue modal PySide6 de personnalisation d'une salade composée.
    Sélection des ingrédients disponibles par catégorie.

Author :
    Dracudar

Version:
    1.3

Date de création :
    2026.06.05

Date de modification:
    2026.06.19
"""

from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.utils.tactile import BoutonIngredientTactile, ScrollAreaTactile
from src.utils import styles_plats


# ── Feuilles de style ──────────────────────────────────────────────────────────
# Styles communs centralisés dans src/utils/styles_plats.py.

_DIALOG_STYLE = styles_plats.DIALOG_STYLE
_BTN_STYLE = styles_plats.BTN_STYLE
_VALIDATE_BTN_STYLE = styles_plats.VALIDATE_BTN_STYLE

_INGREDIENT_BTN_STYLE = styles_plats.style_bouton_toggle(
    font_size=12, padding="4px 10px", min_height=28, text_align="left"
)

_TITLE_STYLE = styles_plats.TITLE_STYLE
_SECTION_STYLE = styles_plats.SECTION_STYLE
_CATEGORY_STYLE = styles_plats.CATEGORY_STYLE
_PRIX_TOTAL_STYLE = styles_plats.PRIX_TOTAL_STYLE
_WARNING_STYLE = styles_plats.WARNING_STYLE

SUPPLEMENT_VIANDE = styles_plats.SUPPLEMENT_VIANDE


# ── Dialogue ───────────────────────────────────────────────────────────────────

class SaladeDialog(QDialog):
    """Dialogue modal de personnalisation d'une salade composée.

    Utilisation :
        dialog = SaladeDialog(prix, stock_ingredients, parent)
        if dialog.exec() == QDialog.Accepted:
            plat_dict = dialog.result_data
    """

    def __init__(
        self,
        prix: float,
        stock_ingredients: Dict[str, List[str]],
        parent=None,
    ):
        """
        Args:
            prix: Prix de la salade depuis la carte active.
            stock_ingredients: Ingrédients disponibles par catégorie depuis le stock.
            parent: Widget parent Qt.
        """
        super().__init__(parent)
        self.prix = prix
        self.stock_ingredients = stock_ingredients
        self.result_data: Optional[Dict] = None

        self._ingredient_cbs: Dict[str, QPushButton] = {}
        self._viande_btns: Dict[str, QPushButton] = {}
        self._warning_label: Optional[QLabel] = None
        self._prix_label: Optional[QLabel] = None

        self.setWindowTitle("Salade composée")
        self.setModal(True)
        self.setStyleSheet(_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(10)

        # Titre
        title = QLabel("Salade composée")
        title.setStyleSheet(_TITLE_STYLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        # Zone ingrédients scrollable
        ingr_widget = self._build_ingredients_scroll()
        if ingr_widget:
            root.addWidget(ingr_widget, stretch=1)

        # Avertissement (masqué par défaut)
        self._warning_label = QLabel("Veuillez sélectionner au moins un ingrédient.")
        self._warning_label.setStyleSheet(_WARNING_STYLE)
        self._warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._warning_label.setVisible(False)
        root.addWidget(self._warning_label)

        # Prix (mis à jour dynamiquement)
        self._prix_label = QLabel()
        self._prix_label.setStyleSheet(_PRIX_TOTAL_STYLE)
        self._prix_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self._prix_label)
        self._update_prix_display()

        # Boutons [Annuler] ──── [Valider]
        actions = QHBoxLayout()
        actions.setSpacing(8)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet(_BTN_STYLE)
        cancel_btn.clicked.connect(self.reject)
        actions.addWidget(cancel_btn)

        actions.addStretch()

        validate_btn = QPushButton("Valider")
        validate_btn.setStyleSheet(_VALIDATE_BTN_STYLE)
        validate_btn.clicked.connect(self._validate)
        actions.addWidget(validate_btn)

        root.addLayout(actions)

        self.resize(400, 500)

    # ──────────────────────────────── Ingrédients ─────────────────────────────

    def _build_ingredients_scroll(self) -> Optional[QWidget]:
        """Construit la zone scrollable des ingrédients par catégorie."""
        if not any(self.stock_ingredients.values()):
            return None

        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel("Ingrédients :")
        lbl.setStyleSheet(_SECTION_STYLE)
        layout.addWidget(lbl)

        scroll = ScrollAreaTactile()

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(3)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(scroll_widget)

        for cat, items in self.stock_ingredients.items():
            if not items:
                continue
            cat_lbl = QLabel(cat)
            cat_lbl.setStyleSheet(_CATEGORY_STYLE)
            scroll_layout.addWidget(cat_lbl)
            for ingr in items:
                btn = BoutonIngredientTactile(ingr, scroll)
                btn.setStyleSheet(_INGREDIENT_BTN_STYLE)
                btn.setCheckable(True)
                btn.setChecked(False)
                scroll_layout.addWidget(btn)
                self._ingredient_cbs[ingr] = btn
                if cat == "Viande":
                    self._viande_btns[ingr] = btn
                    btn.toggled.connect(self._update_prix_display)

        layout.addWidget(scroll)
        return frame

    # ──────────────────────────────── Prix dynamique ──────────────────────────

    def _update_prix_display(self):
        """Met à jour l'étiquette de prix en fonction des viandes sélectionnées."""
        if self._prix_label is None:
            return
        nb_viandes = sum(1 for btn in self._viande_btns.values() if btn.isChecked())
        supplement = nb_viandes * SUPPLEMENT_VIANDE
        total = self.prix + supplement
        if supplement > 0:
            self._prix_label.setText(
                f"Prix : {self.prix:.2f} € + {supplement:.2f} € (viande) = {total:.2f} €"
            )
        else:
            self._prix_label.setText(f"Prix : {self.prix:.2f} €")

    # ──────────────────────────────── Validation ──────────────────────────────

    def _validate(self):
        """Vérifie la sélection, construit le dict de plat et accepte le dialogue."""
        ingredients = [n for n, cb in self._ingredient_cbs.items() if cb.isChecked()]

        if not ingredients:
            self._warning_label.setVisible(True)
            return

        self._warning_label.setVisible(False)

        nom = f"Salade composée : {', '.join(ingredients)}"

        nb_viandes = sum(1 for n in ingredients if n in self._viande_btns)
        prix_final = self.prix + nb_viandes * SUPPLEMENT_VIANDE

        self.result_data = {
            "Plat": "Salade composée",
            "Nom": nom,
            "Prix": prix_final,
            "Statut": "En attente",
            "Composition": {
                "Ingrédients": ingredients,
            },
        }

        self.accept()
