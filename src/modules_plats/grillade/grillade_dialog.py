#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grillade_dialog.py

Description:
    Dialogue modal PySide6 de personnalisation d'une grillade.
    Sélection des viandes par quantité avec limite de 2 portions au total
    (basée sur la valeur de portion de chaque viande).

Author :
    Dracudar

Version:
    1.3

Date de création :
    2026.06.06

Date de modification:
    2026.06.15
"""

from typing import Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QGridLayout,
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

_COUNTER_BTN_STYLE = """
    QPushButton {
        background-color: #4f545e;
        border: 2px solid #7d8390;
        border-radius: 5px;
        color: #f5f5f5;
        font-size: 14px;
        font-weight: 700;
        min-width: 32px;
        min-height: 32px;
        padding: 0px;
    }
    QPushButton:hover { background-color: #626978; border-color: #8fa3b6; }
    QPushButton:pressed { background-color: #3a3d43; }
    QPushButton:disabled {
        background-color: #3a3d43;
        border-color: #4f545e;
        color: #7d8390;
    }
"""

_TITLE_STYLE = "font-size: 18px; font-weight: 700; color: #f5f5f5;"
_SECTION_STYLE = "font-size: 14px; font-weight: 700; color: #f5f5f5;"
_VIANDE_NAME_STYLE = "font-size: 13px; color: #f5f5f5;"
_QUANTITE_STYLE = "font-size: 14px; font-weight: 700; color: #f5f5f5; min-width: 24px;"
_LAST_STOCK_STYLE = "font-size: 11px; color: #e0a030; font-style: italic;"
_PRIX_TOTAL_STYLE = "font-size: 13px; font-weight: 600; color: #a8d08d; padding: 4px 0;"
_WARNING_STYLE = "font-size: 12px; color: #e07070; padding: 2px 0;"
_MAX_PORTIONS_STYLE = "font-size: 12px; color: #a8d08d; padding: 2px 0;"

_ACCOMP_BTN_STYLE = """
    QPushButton {
        background-color: transparent;
        border: 2px solid #7d8390;
        border-radius: 5px;
        color: #f5f5f5;
        font-size: 13px;
        padding: 6px 16px;
        min-height: 32px;
    }
    QPushButton:hover { border-color: #c0c0c0; }
    QPushButton:checked {
        background-color: #f5f5f5;
        border-color: #f5f5f5;
        color: #2f3136;
        font-weight: 600;
    }
"""

MAX_PORTIONS = 2  # Limite totale de portions (en valeur cumulée)


# ── Dialogue ───────────────────────────────────────────────────────────────────

class GrilladeDialog(QDialog):
    """Dialogue modal de personnalisation d'une grillade.

    Utilisation :
        dialog = GrilladeDialog(prix, grillades_stock, parent)
        if dialog.exec() == QDialog.Accepted:
            plat_dict = dialog.result_data
    """

    def __init__(
        self,
        prix: float,
        grillades_stock: Dict[str, Dict],
        frites_disponibles: bool = True,
        parent=None,
    ):
        """
        Args:
            prix: Prix de la grillade depuis la carte active.
            grillades_stock: Dict des viandes disponibles avec leur Valeur et Quantité.
                             Ex: {"Poitrine": {"Valeur": 1, "Quantité": 200, "OutOfStock": false}}
            frites_disponibles: False si les frites sont hors stock (option accompagnement désactivée).
            parent: Widget parent Qt.
        """
        super().__init__(parent)
        self.prix = prix
        self.grillades_stock = grillades_stock
        self.frites_disponibles = frites_disponibles
        self.result_data: Optional[Dict] = None

        # Quantités sélectionnées par viande {nom: int}
        self._quantites: Dict[str, int] = {v: 0 for v in grillades_stock}
        # Références aux widgets de chaque ligne de viande
        self._qtl_labels: Dict[str, QLabel] = {}
        self._btn_plus: Dict[str, QPushButton] = {}
        self._btn_moins: Dict[str, QPushButton] = {}

        self._accompagnement: str = "Frites" if frites_disponibles else "Sans"
        self._accomp_btns: Dict[str, QPushButton] = {}

        self._warning_label: Optional[QLabel] = None
        self._prix_label: Optional[QLabel] = None
        self._portions_label: Optional[QLabel] = None

        self.setWindowTitle("Grillade")
        self.setModal(True)
        self.setStyleSheet(_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        # Titre
        title = QLabel("Grillade")
        title.setStyleSheet(_TITLE_STYLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        # Sous-titre max portions
        self._portions_label = QLabel(f"Sélectionnez vos viandes (max {MAX_PORTIONS} portions) :")
        self._portions_label.setStyleSheet(_SECTION_STYLE)
        root.addWidget(self._portions_label)

        # Lignes de viandes
        viandes_widget = self._build_viandes_rows()
        root.addWidget(viandes_widget)

        # Accompagnement
        accomp_widget = self._build_accompagnement_row()
        root.addWidget(accomp_widget)

        root.addStretch()

        # Avertissement (masqué par défaut)
        self._warning_label = QLabel("Veuillez sélectionner au moins une viande.")
        self._warning_label.setStyleSheet(_WARNING_STYLE)
        self._warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._warning_label.setVisible(False)
        root.addWidget(self._warning_label)

        # Prix (statique pour les grillades)
        self._prix_label = QLabel(f"Prix : {self.prix:.2f} €")
        self._prix_label.setStyleSheet(_PRIX_TOTAL_STYLE)
        self._prix_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self._prix_label)

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

        self.setFixedWidth(380)

    # ──────────────────────────────── Lignes de viandes ───────────────────────

    def _build_viandes_rows(self) -> QWidget:
        """Construit les lignes [Nom] [stretch] [−] [Quantité] [+] pour chaque viande.

        Colonnes du QGridLayout :
            0 : nom de la viande
            1 : espace flexible (stretch) — "Dernier !" s'y loge, aligné à droite
            2 : bouton "−"  /  "Hors stock" centré sur cols 2-4
            3 : label quantité
            4 : bouton "+" (ancré au bord droit pour toutes les lignes)
        """
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setVerticalSpacing(8)
        layout.setHorizontalSpacing(8)
        layout.setColumnStretch(1, 1)

        for row_idx, (viande, data) in enumerate(self.grillades_stock.items()):
            out_of_stock = data.get("OutOfStock", False)
            quantite_stock = data.get("Quantité", 0)

            # Colonne 0 : nom de la viande
            name_lbl = QLabel(viande)
            name_lbl.setStyleSheet(_VIANDE_NAME_STYLE)
            layout.addWidget(name_lbl, row_idx, 0)

            if out_of_stock or quantite_stock == 0:
                # Colonnes 2-4 : "Hors stock" centré sur la zone des boutons
                oos_lbl = QLabel("Hors stock")
                oos_lbl.setStyleSheet("font-size: 11px; color: #e07070; font-style: italic;")
                oos_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(oos_lbl, row_idx, 2, 1, 3)
            else:
                # Colonne 1 : "Dernier !" dans l'espace flexible, aligné à droite des boutons
                if quantite_stock == 1:
                    last_lbl = QLabel("Dernier !")
                    last_lbl.setStyleSheet(_LAST_STOCK_STYLE)
                    last_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    layout.addWidget(last_lbl, row_idx, 1)

                # Colonne 2 : bouton "−"
                btn_moins = QPushButton("−")
                btn_moins.setStyleSheet(_COUNTER_BTN_STYLE)
                btn_moins.setEnabled(False)
                btn_moins.clicked.connect(lambda _, v=viande: self._ajuster(v, -1))
                layout.addWidget(btn_moins, row_idx, 2)
                self._btn_moins[viande] = btn_moins

                # Colonne 3 : label quantité
                qtl_lbl = QLabel("0")
                qtl_lbl.setStyleSheet(_QUANTITE_STYLE)
                qtl_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(qtl_lbl, row_idx, 3)
                self._qtl_labels[viande] = qtl_lbl

                # Colonne 4 : bouton "+"
                btn_plus = QPushButton("+")
                btn_plus.setStyleSheet(_COUNTER_BTN_STYLE)
                btn_plus.clicked.connect(lambda _, v=viande: self._ajuster(v, 1))
                layout.addWidget(btn_plus, row_idx, 4)
                self._btn_plus[viande] = btn_plus

        return container

    # ──────────────────────────────── Accompagnement ─────────────────────────

    def _build_accompagnement_row(self) -> QWidget:
        """Construit la ligne de sélection de l'accompagnement (Frites / Sans)."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel("Accompagnement :")
        lbl.setStyleSheet(_SECTION_STYLE)
        layout.addWidget(lbl)

        layout.addStretch()

        group = QButtonGroup(self)

        for choix in ("Frites", "Sans"):
            btn = QPushButton(choix)
            btn.setStyleSheet(_ACCOMP_BTN_STYLE)
            btn.setCheckable(True)
            btn.setChecked(choix == self._accompagnement)
            if choix == "Frites" and not self.frites_disponibles:
                btn.setEnabled(False)
                btn.setToolTip("Hors stock")
            else:
                btn.clicked.connect(lambda _, c=choix: self._select_accompagnement(c))
            group.addButton(btn)
            layout.addWidget(btn)
            self._accomp_btns[choix] = btn

        return container

    def _select_accompagnement(self, choix: str):
        self._accompagnement = choix
        for c, btn in self._accomp_btns.items():
            btn.setChecked(c == choix)

    # ──────────────────────────────── Logique quantités ───────────────────────

    def _total_portions(self) -> int:
        """Retourne le total de portions sélectionnées (somme des Valeur × quantité)."""
        total = 0
        for viande, qte in self._quantites.items():
            valeur = self.grillades_stock[viande].get("Valeur", 1)
            total += qte * valeur
        return total

    def _ajuster(self, viande: str, delta: int):
        """Incrémente ou décrémente la quantité d'une viande dans les limites autorisées."""
        data = self.grillades_stock[viande]
        valeur = data.get("Valeur", 1)
        quantite_stock = data.get("Quantité", 0)
        qte_actuelle = self._quantites[viande]
        nouvelle_qte = qte_actuelle + delta

        if nouvelle_qte < 0 or nouvelle_qte > quantite_stock:
            return

        # Vérifier la limite totale de portions
        total_sans_viande = self._total_portions() - qte_actuelle * valeur
        if total_sans_viande + nouvelle_qte * valeur > MAX_PORTIONS:
            return

        self._quantites[viande] = nouvelle_qte
        self._qtl_labels[viande].setText(str(nouvelle_qte))
        self._refresh_buttons()

    def _refresh_buttons(self):
        """Met à jour l'état activé/désactivé de tous les boutons +/−."""
        total = self._total_portions()

        for viande in self._btn_plus:
            data = self.grillades_stock[viande]
            valeur = data.get("Valeur", 1)
            quantite_stock = data.get("Quantité", 0)
            qte = self._quantites[viande]

            peut_ajouter = (
                qte < quantite_stock
                and total + valeur <= MAX_PORTIONS
            )
            self._btn_plus[viande].setEnabled(peut_ajouter)
            self._btn_moins[viande].setEnabled(qte > 0)

    # ──────────────────────────────── Validation ──────────────────────────────

    def _validate(self):
        """Vérifie la sélection, construit le dict de plat et accepte le dialogue."""
        viandes_choisies = {v: q for v, q in self._quantites.items() if q > 0}

        if not viandes_choisies:
            self._warning_label.setVisible(True)
            return

        self._warning_label.setVisible(False)

        parties = [
            f"{q} {v}" if q > 1 else v
            for v, q in viandes_choisies.items()
        ]
        viandes_str = " et ".join(parties)
        if self._accompagnement == "Sans":
            nom = f"Grillade : {viandes_str} sans accompagnement"
        else:
            nom = f"Grillade : {viandes_str} avec {self._accompagnement}"

        self.result_data = {
            "Plat": "Grillade",
            "Nom": nom,
            "Prix": self.prix,
            "Statut": "En attente",
            "Composition": {
                "Viandes": viandes_choisies,
                "Accompagnement": self._accompagnement,
            },
        }

        self.accept()
