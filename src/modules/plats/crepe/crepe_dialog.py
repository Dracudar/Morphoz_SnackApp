#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crepe_dialog.py

Description:
    Dialogue modal PySide6 de personnalisation d'une crêpe.
    La crêpe nature est toujours disponible ; les garnitures sont des suppléments
    dont le prix s'ajoute au prix de base.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.06

Date de modification:
    2026.06.06
"""

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
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

_GARNITURE_BTN_STYLE = """
    QPushButton {
        background-color: transparent;
        border: 2px solid #7d8390;
        border-radius: 5px;
        color: #f5f5f5;
        font-size: 13px;
        padding: 6px 14px;
        min-height: 36px;
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
_PRIX_SUPPLEMENT_STYLE = "font-size: 11px; color: #a8d08d;"
_PRIX_TOTAL_STYLE = "font-size: 13px; font-weight: 600; color: #a8d08d; padding: 4px 0;"


# ── Dialogue ───────────────────────────────────────────────────────────────────

class CrepeDialog(QDialog):
    """Dialogue modal de personnalisation d'une crêpe.

    La crêpe nature (sans garniture) est toujours valide.
    Chaque garniture sélectionnée ajoute son prix au prix de base.

    Utilisation :
        dialog = CrepeDialog(prix_base, garnitures, parent)
        if dialog.exec() == QDialog.Accepted:
            plat_dict = dialog.result_data
    """

    def __init__(
        self,
        prix_base: float,
        garnitures: Dict[str, float],
        parent=None,
    ):
        """
        Args:
            prix_base: Prix de la crêpe nature depuis la carte active.
            garnitures: Dict {nom_garniture: prix_supplément} des garnitures disponibles.
            parent: Widget parent Qt.
        """
        super().__init__(parent)
        self.prix_base = prix_base
        self.garnitures = garnitures
        self.result_data: Optional[Dict] = None

        self._garniture_btns: Dict[str, QPushButton] = {}
        self._btn_group: Optional[QButtonGroup] = None
        self._prix_label: Optional[QLabel] = None

        self.setWindowTitle("Crêpe")
        self.setModal(True)
        self.setStyleSheet(_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Titre
        title = QLabel("Crêpe")
        title.setStyleSheet(_TITLE_STYLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        # Section garnitures
        if self.garnitures:
            root.addWidget(self._build_garnitures_section())

        # Affichage du prix total (mis à jour dynamiquement)
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

        # +1 pour l'option "Nature"
        self.resize(360, 120 + (len(self.garnitures) + 1) * 48)

    # ──────────────────────────────── Garnitures ──────────────────────────────

    def _build_garnitures_section(self) -> QWidget:
        """Construit la section de sélection des garnitures (choix unique + nature)."""
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        lbl = QLabel("Garniture :")
        lbl.setStyleSheet(_SECTION_STYLE)
        layout.addWidget(lbl)

        # Groupe exclusif : une seule option cochée à la fois
        self._btn_group = QButtonGroup(frame)
        self._btn_group.setExclusive(True)

        # Option "Nature" (sélectionnée par défaut)
        nature_btn = self._create_option_btn("Nature", self.prix_base, supplement=False)
        nature_btn.setChecked(True)
        self._btn_group.addButton(nature_btn)
        layout.addWidget(nature_btn)
        self._garniture_btns["Nature"] = nature_btn

        for nom, prix in self.garnitures.items():
            btn = self._create_option_btn(nom, prix)
            self._btn_group.addButton(btn)
            layout.addWidget(btn)
            self._garniture_btns[nom] = btn

        self._btn_group.buttonToggled.connect(lambda _btn, _checked: self._update_prix_display())

        return frame

    def _create_option_btn(self, nom: str, prix: Optional[float], supplement: bool = True) -> QPushButton:
        """Crée un bouton d'option (nature ou garniture) avec nom et prix."""
        btn = QPushButton()
        btn.setStyleSheet(_GARNITURE_BTN_STYLE)
        btn.setCheckable(True)

        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(8, 2, 8, 2)
        btn_layout.setSpacing(8)

        nom_lbl = QLabel(nom)
        nom_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        btn_layout.addWidget(nom_lbl)

        btn_layout.addStretch()

        prix_lbl: Optional[QLabel] = None
        if prix is not None:
            texte_prix = f"+{prix:.2f} €" if supplement else f"{prix:.2f} €"
            prix_lbl = QLabel(texte_prix)
            prix_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            btn_layout.addWidget(prix_lbl)

        def _sync_colors(checked: bool):
            text_color = "#2f3136" if checked else "#f5f5f5"
            nom_lbl.setStyleSheet(
                f"font-size: 13px; background-color: transparent; color: {text_color};"
            )
            if prix_lbl:
                prix_color = "#2f3136" if checked else "#a8d08d"
                prix_lbl.setStyleSheet(
                    f"font-size: 11px; background-color: transparent; color: {prix_color};"
                )

        _sync_colors(False)
        btn.toggled.connect(_sync_colors)

        return btn

    # ──────────────────────────────── Prix dynamique ──────────────────────────

    def _update_prix_display(self):
        """Met à jour l'étiquette de prix en fonction de la garniture sélectionnée."""
        if self._prix_label is None:
            return
        garniture = self._selected_garniture()
        if garniture:
            supplement = self.garnitures[garniture]
            total = self.prix_base + supplement
            self._prix_label.setText(
                f"Prix : {self.prix_base:.2f} € + {supplement:.2f} € = {total:.2f} €"
            )
        else:
            self._prix_label.setText(f"Prix : {self.prix_base:.2f} €")

    def _selected_garniture(self) -> Optional[str]:
        """Retourne le nom de la garniture sélectionnée, ou None si 'Nature'."""
        for nom, btn in self._garniture_btns.items():
            if btn.isChecked() and nom != "Nature":
                return nom
        return None

    # ──────────────────────────────── Validation ──────────────────────────────

    def _validate(self):
        """Construit le dict de plat et accepte le dialogue."""
        garniture = self._selected_garniture()

        if garniture:
            supplement = self.garnitures[garniture]
            prix_final = self.prix_base + supplement
            nom = f"Crêpe {garniture}"
            garnitures_liste = [garniture]
        else:
            prix_final = self.prix_base
            nom = "Crêpe nature"
            garnitures_liste = []

        self.result_data = {
            "Plat": "Crêpe",
            "Nom": nom,
            "Prix": prix_final,
            "Statut": "En attente",
            "Composition": {
                "Garniture": garnitures_liste,
            },
        }

        self.accept()
