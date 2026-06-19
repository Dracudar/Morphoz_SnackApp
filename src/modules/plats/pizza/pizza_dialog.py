#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pizza_dialog.py

Description:
    Dialogue modal PySide6 de sélection et personnalisation d'une pizza.
    Étape 1 : sélection de la recette.
    Étape 2 : personnalisation de la base et des ingrédients.

Author :
    Dracudar

Version:
    1.7

Date de création :
    2026.06.05

Date de modification:
    2026.06.19
"""

from typing import Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.utils.tactile import BoutonIngredientTactile, ScrollAreaTactile
from src.utils import styles_plats


# ── Feuilles de style ──────────────────────────────────────────────────────────
# Styles communs centralisés dans src/utils/styles_plats.py ; seuls les styles
# propres à la pizza (recette, base) restent définis ici.

_DIALOG_STYLE = styles_plats.DIALOG_STYLE
_BTN_STYLE = styles_plats.BTN_STYLE

_RECIPE_BTN_STYLE = """
    QPushButton {
        background-color: #4f545e;
        border: 2px solid #7d8390;
        border-radius: 8px;
        color: #f5f5f5;
        padding: 12px 18px;
        min-height: 64px;
        min-width: 130px;
    }
    QPushButton:hover { background-color: #626978; border-color: #8fa3b6; }
    QPushButton:pressed { background-color: #3a3d43; }
"""

_VALIDATE_BTN_STYLE = styles_plats.VALIDATE_BTN_STYLE

_RADIO_STYLE = """
    QRadioButton {
        color: #f5f5f5;
        font-size: 13px;
        spacing: 0px;
        padding: 5px 14px;
        border: 2px solid #7d8390;
        border-radius: 14px;
        background-color: transparent;
    }
    QRadioButton:hover {
        border-color: #c0c0c0;
    }
    QRadioButton:checked {
        border-color: #f5f5f5;
        background-color: rgba(245, 245, 245, 0.15);
    }
    QRadioButton::indicator {
        width: 0px;
        height: 0px;
        image: none;
    }
"""

_INGREDIENT_BTN_STYLE = styles_plats.style_bouton_toggle(
    font_size=12, padding="4px 10px", min_height=28, text_align="left"
)
_TITLE_STYLE = styles_plats.TITLE_STYLE
_SECTION_STYLE = styles_plats.SECTION_STYLE
_CATEGORY_STYLE = styles_plats.CATEGORY_STYLE
_PRICE_STYLE = styles_plats.PRICE_STYLE
_PRIX_TOTAL_STYLE = styles_plats.PRIX_TOTAL_STYLE

SUPPLEMENT_VIANDE = styles_plats.SUPPLEMENT_VIANDE


# ── Dialogue ───────────────────────────────────────────────────────────────────

class PizzaDialog(QDialog):
    """Dialogue modal de sélection de recette et personnalisation d'une pizza.

    Utilisation :
        dialog = PizzaDialog(recettes, bases, stock_ingredients, parent)
        if dialog.exec() == QDialog.Accepted:
            plat_dict = dialog.result_data
    """

    def __init__(
        self,
        recettes: Dict,
        bases: List[str],
        stock_ingredients: Dict[str, List[str]],
        parent=None,
    ):
        """
        Args:
            recettes: Dict des recettes (carte_active.json → Pizza.Recettes).
            bases: Bases disponibles depuis le stock (filtrées hors-stock).
            stock_ingredients: Ingrédients disponibles par catégorie depuis le stock.
            parent: Widget parent Qt.
        """
        super().__init__(parent)
        self.recettes = recettes
        self.bases = bases
        self.stock_ingredients = stock_ingredients
        self.result_data: Optional[Dict] = None

        # Widgets de saisie reconstruits à chaque étape 2
        self._base_radios: Dict[str, QRadioButton] = {}
        self._ingredient_cbs: Dict[str, QPushButton] = {}
        self._viande_btns: Dict[str, QPushButton] = {}
        self._recette_ingr: set = set()  # ingrédients natifs de la recette sélectionnée
        self._prix_base: float = 0.0
        self._prix_label: Optional[QLabel] = None

        self.setWindowTitle("Pizza")
        self.setModal(True)
        self.setStyleSheet(_DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_step1())
        root.addWidget(self._stack)

        self.resize(480, 340)

    # ──────────────────────────────── Étape 1 ─────────────────────────────────

    def _build_step1(self) -> QWidget:
        """Construit la page de sélection de recette."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Choisissez une recette")
        title.setStyleSheet(_TITLE_STYLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Grille de boutons de recettes
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)

        available = [
            (nom, data) for nom, data in self.recettes.items()
            if data.get("Etat", "Disponible") not in ("Hors stock", "Retiré", "Archivé")
        ]

        cols = 3
        for idx, (nom, data) in enumerate(available):
            btn = self._create_recipe_button(nom, data)
            btn.clicked.connect(
                lambda _=False, n=nom, d=data: self._on_recipe_selected(n, d)
            )
            row, col = divmod(idx, cols)
            grid.addWidget(btn, row, col)

        layout.addWidget(grid_widget)
        layout.addStretch()

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet(_BTN_STYLE)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        return page

    def _create_recipe_button(self, nom: str, data: Dict) -> QPushButton:
        """Crée un bouton de recette avec nom et prix."""
        btn = QPushButton()
        btn.setStyleSheet(_RECIPE_BTN_STYLE)

        btn_layout = QVBoxLayout(btn)
        btn_layout.setSpacing(3)
        btn_layout.setContentsMargins(8, 8, 8, 8)

        name_lbl = QLabel(nom)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #f5f5f5;")
        name_lbl.setWordWrap(True)
        btn_layout.addWidget(name_lbl)

        prix = data.get("Prix")
        if prix is not None:
            price_lbl = QLabel(f"{prix:.2f} €")
            price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_lbl.setStyleSheet(_PRICE_STYLE)
            btn_layout.addWidget(price_lbl)

        return btn

    def _on_recipe_selected(self, nom: str, data: Dict):
        """Passe à l'étape de personnalisation pour la recette choisie."""
        if self._stack.count() > 1:
            old = self._stack.widget(1)
            self._stack.removeWidget(old)
            old.deleteLater()

        self._stack.addWidget(self._build_step2(nom, data))
        self._stack.setCurrentIndex(1)
        self.resize(500, 580)

    # ──────────────────────────────── Étape 2 ─────────────────────────────────

    def _build_step2(self, nom_recette: str, recette_data: Dict) -> QWidget:
        """Construit la page de personnalisation (base en ligne, ingrédients en dessous)."""
        self._base_radios = {}
        self._ingredient_cbs = {}
        self._viande_btns = {}
        self._recette_ingr = set(recette_data.get("Ingrédients", []))
        self._prix_base = recette_data.get("Prix", 0.0)
        self._prix_label = None

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Titre
        title = QLabel(f"Pizza {nom_recette}")
        title.setStyleSheet(_TITLE_STYLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        recette_bases = recette_data.get("Base", [])
        recette_ingr = set(recette_data.get("Ingrédients", []))

        # Section base (radio buttons en ligne horizontale)
        if self.bases:
            layout.addWidget(self._build_base_row(recette_bases))

        # Section ingrédients (scroll, prend le reste de la hauteur)
        ingr_widget = self._build_ingredients_scroll(recette_ingr)
        if ingr_widget:
            layout.addWidget(ingr_widget, stretch=1)

        # Affichage du prix total (mis à jour dynamiquement)
        self._prix_label = QLabel()
        self._prix_label.setStyleSheet(_PRIX_TOTAL_STYLE)
        self._prix_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._prix_label)
        self._update_prix_display()

        # Boutons actions : [Annuler] [← Retour] ──── [Valider]
        actions = QHBoxLayout()
        actions.setSpacing(8)

        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet(_BTN_STYLE)
        cancel_btn.clicked.connect(self.reject)
        actions.addWidget(cancel_btn)

        back_btn = QPushButton("← Retour")
        back_btn.setStyleSheet(_BTN_STYLE)
        back_btn.clicked.connect(lambda: (self._stack.setCurrentIndex(0), self.resize(480, 340)))
        actions.addWidget(back_btn)

        actions.addStretch()

        validate_btn = QPushButton("Valider")
        validate_btn.setStyleSheet(_VALIDATE_BTN_STYLE)
        validate_btn.clicked.connect(lambda: self._validate(nom_recette, recette_data))
        actions.addWidget(validate_btn)

        layout.addLayout(actions)
        return page

    def _build_base_row(self, recette_bases: List[str]) -> QWidget:
        """Construit la section de sélection de la base en ligne horizontale."""
        frame = QWidget()
        row = QHBoxLayout(frame)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(16)

        lbl = QLabel("Base :")
        lbl.setStyleSheet(_SECTION_STYLE)
        lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        row.addWidget(lbl)

        group = QButtonGroup(frame)
        default = recette_bases[0] if recette_bases else self.bases[0]

        for base in self.bases:
            radio = QRadioButton(base)
            radio.setStyleSheet(_RADIO_STYLE)
            radio.setChecked(base == default)
            group.addButton(radio)
            row.addWidget(radio)
            self._base_radios[base] = radio

        row.addStretch()
        return frame

    def _build_ingredients_scroll(self, recette_ingr: set) -> Optional[QWidget]:
        """Construit la zone scrollable des ingrédients.

        Affiche en premier les ingrédients propres à la recette (absents du stock
        disponible), puis les ingrédients du stock par catégorie.
        """
        all_stock_ingr = {i for items in self.stock_ingredients.values() for i in items}
        recette_only = [i for i in recette_ingr if i not in all_stock_ingr]

        has_content = recette_only or any(self.stock_ingredients.values())
        if not has_content:
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

        # Ingrédients propres à la recette (hors stock)
        if recette_only:
            cat_lbl = QLabel("Recette")
            cat_lbl.setStyleSheet(_CATEGORY_STYLE)
            scroll_layout.addWidget(cat_lbl)
            for ingr in sorted(recette_only):
                btn = BoutonIngredientTactile(ingr, scroll)
                btn.setStyleSheet(_INGREDIENT_BTN_STYLE)
                btn.setCheckable(True)
                btn.setChecked(True)
                scroll_layout.addWidget(btn)
                self._ingredient_cbs[ingr] = btn

        # Ingrédients du stock par catégorie
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
                btn.setChecked(ingr in recette_ingr)
                scroll_layout.addWidget(btn)
                self._ingredient_cbs[ingr] = btn
                if cat == "Viande":
                    self._viande_btns[ingr] = btn
                    btn.toggled.connect(self._update_prix_display)

        layout.addWidget(scroll)
        return frame

    # ──────────────────────────────── Prix dynamique ──────────────────────────

    def _update_prix_display(self):
        """Met à jour l'étiquette de prix en fonction des viandes sélectionnées.

        Logique supplément :
        - Viande native décochée  → -1 € (retrait d'un ingrédient inclus dans le prix de base)
        - Viande ajoutée cochée   → +1 € (supplément)
        """
        if self._prix_label is None:
            return
        viandes_retirees = sum(
            1 for ingr, btn in self._viande_btns.items()
            if ingr in self._recette_ingr and not btn.isChecked()
        )
        viandes_ajoutees = sum(
            1 for ingr, btn in self._viande_btns.items()
            if ingr not in self._recette_ingr and btn.isChecked()
        )
        delta = (viandes_ajoutees - viandes_retirees) * SUPPLEMENT_VIANDE
        total = self._prix_base + delta

        parts = []
        if viandes_ajoutees:
            parts.append(f"+ {viandes_ajoutees * SUPPLEMENT_VIANDE:.2f} € (viande supp.)")
        if viandes_retirees:
            parts.append(f"- {viandes_retirees * SUPPLEMENT_VIANDE:.2f} € (viande retirée)")

        if parts:
            self._prix_label.setText(
                f"Prix : {self._prix_base:.2f} € {' '.join(parts)} = {total:.2f} €"
            )
        else:
            self._prix_label.setText(f"Prix : {self._prix_base:.2f} €")

    # ──────────────────────────────── Validation ──────────────────────────────

    def _validate(self, nom_recette: str, recette_data: Dict):
        """Construit le dict de plat et accepte le dialogue."""
        # Base sélectionnée
        base = next(
            (b for b, r in self._base_radios.items() if r.isChecked()), ""
        )

        # Ingrédients sélectionnés
        ingredients = [n for n, cb in self._ingredient_cbs.items() if cb.isChecked()]

        # Calcul des modifications par rapport à la recette
        recette_bases_defaut = recette_data.get("Base", [])
        recette_ingr_defaut = set(recette_data.get("Ingrédients", []))
        ingr_set = set(ingredients)
        ingr_retires = recette_ingr_defaut - ingr_set
        ingr_supplementaires = ingr_set - recette_ingr_defaut

        # Nom affiché de la pizza
        nom = self._build_display_name(
            nom_recette, base, ingredients, recette_bases_defaut,
            ingr_retires, ingr_supplementaires,
        )

        # Champ "Recette" (marqué si modifié)
        recette_field = nom_recette
        if ingr_retires or ingr_supplementaires:
            recette_field = f"{nom_recette} - Modifié !"

        recette_viandes = {n for n in recette_ingr_defaut if n in self._viande_btns}
        viandes_retirees = sum(1 for n in recette_viandes if n not in ingr_set)
        viandes_ajoutees = sum(1 for n in ingr_set if n in self._viande_btns and n not in recette_viandes)
        prix_final = recette_data.get("Prix", 0.0) + (viandes_ajoutees - viandes_retirees) * SUPPLEMENT_VIANDE

        self.result_data = {
            "Plat": "Pizza",
            "Recette": recette_field,
            "Nom": nom,
            "Prix": prix_final,
            "Statut": "En attente",
            "Composition": {
                "Base": base,
                "Ingrédients": ingredients,
                "Ajouts": sorted(ingr_supplementaires),
                "Retraits": sorted(ingr_retires),
            },
        }

        self.accept()

    @staticmethod
    def _build_display_name(
        nom_recette: str,
        base: str,
        ingredients: List[str],
        bases_defaut: List[str],
        ingr_retires: set,
        ingr_supplementaires: set,
    ) -> str:
        """Construit la description lisible de la pizza pour l'affichage commande."""
        if nom_recette == "Personnalisable":
            parts = ["Pizza personnalisée"]
            if base:
                parts.append(f"base {base}")
            if ingredients:
                parts.append(f"avec {', '.join(ingredients)}")
            return " ".join(parts)

        nom = f"Pizza {nom_recette}"
        if base and (not bases_defaut or base != bases_defaut[0]):
            nom += f" base {base}"
        if ingr_retires:
            nom += f" (sans {', '.join(sorted(ingr_retires))})"
        if ingr_supplementaires:
            nom += f" (+ {', '.join(sorted(ingr_supplementaires))})"
        return nom
