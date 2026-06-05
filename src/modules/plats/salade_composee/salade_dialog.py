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
    1.1

Date de création :
    2026.06.05

Date de modification:
    2026.06.06
"""

from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


# ── Feuilles de style ──────────────────────────────────────────────────────────

_DIALOG_STYLE = """
    QDialog {
        background-color: #2f3136;
    }
    QWidget {
        background-color: #2f3136;
        color: #f5f5f5;
    }
    QScrollArea, QScrollArea > QWidget > QWidget {
        background-color: #2f3136;
    }
"""

_BTN_STYLE = """
    QPushButton {
        background-color: #4f545e;
        border: 2px solid #7d8390;
        border-radius: 8px;
        color: #f5f5f5;
        font-size: 13px;
        font-weight: 600;
        padding: 8px 16px;
        min-height: 38px;
    }
    QPushButton:hover { background-color: #626978; border-color: #8fa3b6; }
    QPushButton:pressed { background-color: #3a3d43; }
"""

_VALIDATE_BTN_STYLE = """
    QPushButton {
        background-color: #3a7a3a;
        border: 2px solid #4d9c4d;
        border-radius: 8px;
        color: #f5f5f5;
        font-size: 14px;
        font-weight: 700;
        padding: 10px 24px;
        min-height: 44px;
    }
    QPushButton:hover { background-color: #4d9c4d; }
    QPushButton:pressed { background-color: #2e5e2e; }
"""

_INGREDIENT_BTN_STYLE = """
    QPushButton {
        background-color: transparent;
        border: 2px solid #7d8390;
        border-radius: 5px;
        color: #f5f5f5;
        font-size: 12px;
        padding: 4px 10px;
        min-height: 28px;
        text-align: left;
    }
    QPushButton:hover {
        border-color: #c0c0c0;
    }
    QPushButton:checked {
        background-color: #f5f5f5;
        border-color: #f5f5f5;
        color: #2f3136;
        font-weight: 600;
    }
"""

_TITLE_STYLE = "font-size: 18px; font-weight: 700; color: #f5f5f5;"
_SECTION_STYLE = "font-size: 14px; font-weight: 700; color: #f5f5f5;"
_CATEGORY_STYLE = "font-size: 12px; font-weight: 700; color: #a8d08d; margin-top: 6px;"
_PRIX_TOTAL_STYLE = "font-size: 13px; font-weight: 600; color: #a8d08d; padding: 4px 0;"
_WARNING_STYLE = "font-size: 12px; color: #e07070; padding: 2px 0;"

SUPPLEMENT_VIANDE = 1.0  # € par viande sélectionnée


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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

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
                btn = QPushButton(ingr)
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

        nom = f"Salade composée avec {', '.join(ingredients)}"

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
