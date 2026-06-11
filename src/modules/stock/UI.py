#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI.py - Vue gestion du stock

Description:
    Interface Qt/PySide6 de consultation et gestion du stock.
    Panneau gauche (50 %) : sections pliables par famille, barre de recherche libre.
    Chaque ligne d'article affiche son nom et trois tags fixes alignés à droite :
      - Carte  (coloré si référencé dans la carte active, grisé sinon)
      - Suivi  (coloré si suivi unitaire actif, grisé sinon)
      - État   (En stock / Rupture)
    Panneau droit (50 %) : détail de l'article sélectionné avec formulaire
    d'édition (catégorie, nom, suivi quantité ON/OFF, valeurs de stock,
    statut OutOfStock) et bouton d'enregistrement.

Author :
    Dracudar

Version:
    2.1

Date de création :
    2025.05.29

Date de modification:
    2026.06.10
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.backend import logger
from src.backend.data_sources import (
    get_card_data,
    get_live_orders_prep,
    get_stock_cache,
    get_stock_data,
    save_stock_data,
)

# ── Couleurs ──────────────────────────────────────────────────────────────────
_BG_MAIN        = "#2f3136"
_BG_SECTION     = "#343740"
_BG_RIGHT       = "#2f3136"
_BG_ITEM_OK     = "#3a3d43"
_BG_ITEM_OOS    = "#3d2f2f"
_BG_ITEM_SEL    = "#40454f"
_BORDER_MAIN    = "#7f7f7f"
_BORDER_SECTION = "#60646c"
_BORDER_ITEM    = "#4a4e55"
_BORDER_OOS     = "#7a3030"
_BORDER_SEL     = "#c97a30"
_TEXT_TITLE     = "#f5f5f5"
_TEXT_SECTION   = "#e0e3e8"
_TEXT_SUBGROUP  = "#b0b4bc"
_TEXT_ITEM      = "#d6d6d6"
_TEXT_ITEM_OOS  = "#a08080"
_TEXT_DIM       = "#8a8e96"

# Tags actifs
_CLR_IN_STOCK   = "#4caf50"
_CLR_OOS        = "#c0392b"
_CLR_CARTE_FG   = "#5b9bd5"
_CLR_CARTE_BG   = "#1e2d3d"
_CLR_CARTE_BD   = "#2e5a8a"
_CLR_SUIVI_FG   = "#d4a017"
_CLR_SUIVI_BG   = "#4a3a00"
_CLR_SUIVI_BD   = "#d4a017"

# Tags inactifs (grisés)
_TAG_OFF_BG = "#3b3f46"
_TAG_OFF_BD = "#4a4e55"
_TAG_OFF_FG = "#595d64"

_TAG_W_CARTE = 46
_TAG_W_SUIVI = 46
_TAG_W_ETAT  = 66


# ── Helpers de données ────────────────────────────────────────────────────────

def _build_carte_ingredients_set() -> Set[str]:
    """Collecte tous les noms d'ingrédients référencés dans la carte active."""
    try:
        card = get_card_data()
    except Exception:
        return set()
    names: Set[str] = set()

    def _traverse(node: Any) -> None:
        if not isinstance(node, dict):
            return
        for key in ("Base", "Ingrédients"):
            for name in node.get(key, []):
                if isinstance(name, str):
                    names.add(name)
        for value in node.values():
            if isinstance(value, dict):
                _traverse(value)

    _traverse(card)
    return names


def _build_prep_data() -> Tuple[Dict[Tuple[str, str], int], Dict[str, int]]:
    """
    Construit les compteurs de plats actifs (en préparation / prêts).

    Retourne :
    - by_nom  : {(catégorie_plat, nom_plat) : count}
    - by_plat : {catégorie_plat : count_total}
    """
    by_nom: Dict[Tuple[str, str], int] = {}
    by_plat: Dict[str, int] = {}
    try:
        for item in get_live_orders_prep():
            plat = item.get("plat", "")
            nom  = item.get("nom", "")
            by_nom[(plat, nom)] = by_nom.get((plat, nom), 0) + 1
            by_plat[plat]       = by_plat.get(plat, 0) + 1
    except Exception:
        pass
    return by_nom, by_plat


def _resolve_path(data: Any, path: List[str]) -> Any:
    """Navigue dans un dict imbriqué via une liste de clés."""
    node = data
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def _is_stock_leaf(node: Any) -> bool:
    """Retourne True si le nœud est une feuille de stock (article individuel)."""
    if not isinstance(node, dict):
        return False
    return (
        any(k in node for k in ("Quantité", "OutOfStock", "Valeur"))
        and not any(isinstance(v, dict) and not _is_stock_leaf(v) for v in node.values())
    )


def _get_prep_count(
    path: List[str],
    node: Dict[str, Any],
    by_nom: Dict[Tuple[str, str], int],
    by_plat: Dict[str, int],
) -> int:
    """
    Nombre de portions en préparation / prêtes pour cet article.
    Uniquement pour les plats unitaires (section "Plats" avec Quantité).

    - Avec "Valeur" (grillades) : suivi individuel par nom × Valeur.
    - Sans "Valeur" (ex. pâte à pizza) : total de la sous-catégorie.
    """
    if not path or path[0] != "Plats" or "Quantité" not in node:
        return 0
    if len(path) < 2:
        return 0
    sub_cat   = path[1]
    item_name = path[-1]
    valeur    = node.get("Valeur", 1)
    if "Valeur" in node:
        return by_nom.get((sub_cat, item_name), 0) * valeur
    return by_plat.get(sub_cat, 0)


def _collect_container_paths(data: Dict, prefix: Optional[List[str]] = None) -> List[str]:
    """Retourne tous les chemins de conteneurs (nœuds non-feuilles) du stock."""
    if prefix is None:
        prefix = []
    result: List[str] = []
    for key, value in data.items():
        if isinstance(value, dict) and not _is_stock_leaf(value):
            path = prefix + [key]
            result.append(" > ".join(path))
            result.extend(_collect_container_paths(value, path))
    return result


# ── Widget de ligne cliquable ─────────────────────────────────────────────────

class _ClickableRow(QFrame):
    """QFrame émettant un signal clicked avec son chemin lorsqu'on clique dessus."""

    clicked = Signal(list)

    def __init__(self, path: List[str], parent=None):
        super().__init__(parent)
        self._path = path
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._path)
        super().mousePressEvent(event)


# ── Module principal ──────────────────────────────────────────────────────────

class StockModule(QFrame):
    """Module de consultation et gestion du stock."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("stockModule")
        self._sections_expanded: Dict[str, bool] = {}
        self._selected_path: Optional[List[str]] = None

        # Références vers les labels lecture seule du panneau de détail
        self._detail_fichier_lbl:    Optional[QLabel] = None
        self._detail_cache_lbl:      Optional[QLabel] = None
        self._detail_prep_lbl:       Optional[QLabel] = None
        self._detail_stock_reel_lbl: Optional[QLabel] = None

        self._build_ui()
        self._build_timer()
        self.refresh()

    # ── Construction de l'interface ─────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(8)

        title = QLabel("Gestion du stock")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("sectionTitle")
        main_layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Panneau gauche : recherche + liste ─────────────────────────────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Rechercher un article…")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.textChanged.connect(self.refresh)
        left_layout.addWidget(self.search_field)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet(
            f"QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: {_BG_MAIN}; }}"
        )
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        self.scroll_area.setWidget(self.list_container)
        left_layout.addWidget(self.scroll_area, 1)

        splitter.addWidget(left_widget)

        # ── Panneau droit : détail / édition ───────────────────────────────
        self.right_scroll = QScrollArea()
        self.right_scroll.setWidgetResizable(True)
        self.right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.right_scroll.setStyleSheet(
            f"QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: {_BG_RIGHT}; }}"
        )
        self._detail_widget: Optional[QWidget] = None
        self._show_empty_detail()
        splitter.addWidget(self.right_scroll)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter, 1)

        self.setStyleSheet(
            f"""
            QFrame#stockModule {{
                background-color: {_BG_MAIN};
                border: 1px solid {_BORDER_MAIN};
            }}
            QLabel#sectionTitle {{
                color: {_TEXT_TITLE};
                font-size: 22px;
                font-weight: 700;
                padding: 4px;
            }}
            QLineEdit {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 6px;
                padding: 6px 8px;
            }}
            QComboBox {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 28px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                selection-background-color: #4f545e;
            }}
            QSpinBox {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 28px;
            }}
            QCheckBox {{
                color: {_TEXT_ITEM};
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            """
        )

    def _build_timer(self) -> None:
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(10_000)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()

    # ── Rafraîchissement principal ──────────────────────────────────────────

    def refresh(self) -> None:
        file_data       = get_stock_data()
        cache_obj       = get_stock_cache()
        cache_data      = cache_obj.data if cache_obj is not None else {}
        carte_set       = _build_carte_ingredients_set()
        by_nom, by_plat = _build_prep_data()
        query           = self.search_field.text().strip().lower()

        self._clear_list()
        for section_name, section_node in file_data.items():
            if not isinstance(section_node, dict):
                continue
            section_widget = self._build_section(
                section_name, section_node, carte_set, query,
            )
            if section_widget is not None:
                self.list_layout.insertWidget(self.list_layout.count() - 1, section_widget)

        # Mettre à jour uniquement les labels lecture seule du détail
        self._update_detail_readonly(file_data, cache_data, by_nom, by_plat)

    def _clear_list(self) -> None:
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    # ── Panneau de détail ───────────────────────────────────────────────────

    def _show_empty_detail(self) -> None:
        """Affiche l'état vide dans le panneau de détail."""
        if self._detail_widget is not None:
            self._detail_widget.deleteLater()
        empty = QWidget()
        lyt = QVBoxLayout(empty)
        lbl = QLabel("Sélectionner un article\npour afficher son détail")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 12px;")
        lyt.addStretch()
        lyt.addWidget(lbl)
        lyt.addStretch()
        self.right_scroll.setWidget(empty)
        self._detail_widget         = empty
        self._detail_fichier_lbl    = None
        self._detail_cache_lbl      = None
        self._detail_prep_lbl       = None
        self._detail_stock_reel_lbl = None

    def _build_detail_panel(
        self,
        path: List[str],
        file_data: Dict,
        cache_data: Dict,
        by_nom: Dict,
        by_plat: Dict,
    ) -> None:
        """Construit le formulaire de détail pour l'article sélectionné."""
        if self._detail_widget is not None:
            self._detail_widget.deleteLater()
        self._detail_fichier_lbl    = None
        self._detail_cache_lbl      = None
        self._detail_prep_lbl       = None
        self._detail_stock_reel_lbl = None

        node = _resolve_path(file_data, path)
        if not isinstance(node, dict):
            self._show_empty_detail()
            return

        out_of_stock = node.get("OutOfStock", False)
        has_qty      = "Quantité" in node
        cache_node   = _resolve_path(cache_data, path) or {}
        cache_qty    = cache_node.get("Quantité")
        prep         = _get_prep_count(path, node, by_nom, by_plat)

        oos_state = [out_of_stock]

        content = QWidget()
        lyt = QVBoxLayout(content)
        lyt.setContentsMargins(16, 14, 16, 14)
        lyt.setSpacing(10)

        # ── Titre ────────────────────────────────────────────────────────
        title_lbl = QLabel(path[-1])
        title_lbl.setStyleSheet(
            f"color: {_TEXT_TITLE}; font-size: 15px; font-weight: 700; border: none;"
        )
        cat_lbl = QLabel(" > ".join(path[:-1]))
        cat_lbl.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 11px; border: none;")
        lyt.addWidget(title_lbl)
        lyt.addWidget(cat_lbl)
        lyt.addWidget(self._make_separator())

        # ── Formulaire ───────────────────────────────────────────────────
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.setContentsMargins(0, 0, 0, 0)

        # Catégorie
        all_cats = _collect_container_paths(file_data)
        cat_combo = QComboBox()
        cat_combo.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        cat_combo.addItems(all_cats)
        current_cat = " > ".join(path[:-1])
        idx = next((i for i, c in enumerate(all_cats) if c == current_cat), -1)
        if idx >= 0:
            cat_combo.setCurrentIndex(idx)
        form.addRow(self._form_label("Catégorie :"), cat_combo)

        # Nom
        name_edit = QLineEdit(path[-1])
        form.addRow(self._form_label("Nom :"), name_edit)

        lyt.addLayout(form)
        lyt.addWidget(self._make_separator())

        # ── Suivi quantité ───────────────────────────────────────────────
        suivi_lbl = QLabel("Suivi quantité")
        suivi_lbl.setStyleSheet(
            f"color: {_TEXT_SECTION}; font-size: 13px; font-weight: 700; border: none;"
        )
        lyt.addWidget(suivi_lbl)

        suivi_chk = QCheckBox("Activer le suivi unitaire (quantité)")
        suivi_chk.setChecked(has_qty)
        lyt.addWidget(suivi_chk)

        fichier_qty    = int(node.get("Quantité", 0) or 0)
        stock_reel_val = (cache_qty + prep) if cache_qty is not None else None

        qty_block = QWidget()
        qty_hbox  = QHBoxLayout(qty_block)
        qty_hbox.setContentsMargins(4, 4, 4, 4)
        qty_hbox.setSpacing(16)

        # ── Colonne gauche : compteurs (lecture seule) ─────────────────────
        left_col  = QWidget()
        left_form = QFormLayout(left_col)
        left_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        left_form.setHorizontalSpacing(10)
        left_form.setVerticalSpacing(6)
        left_form.setContentsMargins(0, 0, 0, 0)

        fichier_lbl    = QLabel(str(fichier_qty))
        cache_val_lbl  = QLabel("—" if cache_qty is None else str(cache_qty))
        prep_val_lbl   = QLabel(str(prep))
        stock_reel_lbl = QLabel("—" if stock_reel_val is None else str(stock_reel_val))

        fichier_lbl.setStyleSheet(
            "color: #9b9fa7; font-size: 13px; font-weight: 600; border: none;"
        )
        for lbl, clr in (
            (cache_val_lbl,  "#7ab8e0"),
            (prep_val_lbl,   "#d4a017"),
            (stock_reel_lbl, "#c97a30"),
        ):
            lbl.setStyleSheet(
                f"color: {clr}; font-size: 13px; font-weight: 600; border: none;"
            )

        left_form.addRow(self._form_label("Fichier :"),         fichier_lbl)
        left_form.addRow(self._form_label("Cache (saisie) :"),  cache_val_lbl)
        left_form.addRow(self._form_label("En préparation :"),  prep_val_lbl)
        left_form.addRow(self._form_label("Stock réel :"),      stock_reel_lbl)

        # ── Séparateur vertical ────────────────────────────────────────────
        vsep = QFrame()
        vsep.setFrameShape(QFrame.Shape.VLine)
        vsep.setStyleSheet(
            f"border: none; border-left: 1px solid {_BORDER_SECTION};"
        )

        # ── Colonne droite : modification manuelle du stock réel ───────────
        right_col  = QWidget()
        right_vbox = QVBoxLayout(right_col)
        right_vbox.setContentsMargins(0, 0, 0, 0)
        right_vbox.setSpacing(6)

        update_title = QLabel("Modifier le stock réel")
        update_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        update_title.setStyleSheet(
            f"color: {_TEXT_DIM}; font-size: 11px; font-style: italic; border: none;"
        )
        right_vbox.addWidget(update_title)

        _btn_style = (
            f"QPushButton {{ background-color: #3b3f46; color: {_TEXT_TITLE};"
            f" border: 1px solid #676d79; border-radius: 4px;"
            f" font-size: 12px; font-weight: 700; min-width: 36px; }}"
            f" QPushButton:hover {{ background-color: #4a4e57; }}"
            f" QPushButton:pressed {{ background-color: #555b66; }}"
        )

        stock_reel_spin = QSpinBox()
        stock_reel_spin.setRange(0, 999_999)
        stock_reel_spin.setValue(stock_reel_val if stock_reel_val is not None else fichier_qty)
        stock_reel_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stock_reel_spin.setFixedHeight(32)
        stock_reel_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        btn_m10 = QPushButton("−10")
        btn_m1  = QPushButton("−1")
        btn_p1  = QPushButton("+1")
        btn_p10 = QPushButton("+10")
        for b in (btn_m10, btn_m1, btn_p1, btn_p10):
            b.setFixedHeight(32)
            b.setStyleSheet(_btn_style)

        btn_m10.clicked.connect(lambda: stock_reel_spin.setValue(max(0, stock_reel_spin.value() - 10)))
        btn_m1.clicked.connect(lambda: stock_reel_spin.setValue(max(0, stock_reel_spin.value() - 1)))
        btn_p1.clicked.connect(lambda: stock_reel_spin.setValue(stock_reel_spin.value() + 1))
        btn_p10.clicked.connect(lambda: stock_reel_spin.setValue(stock_reel_spin.value() + 10))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        btn_row.addWidget(btn_m10)
        btn_row.addWidget(btn_m1)
        btn_row.addWidget(stock_reel_spin, 1)
        btn_row.addWidget(btn_p1)
        btn_row.addWidget(btn_p10)
        right_vbox.addLayout(btn_row)

        formula_lbl = QLabel("= Fichier + En préparation")
        formula_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        formula_lbl.setStyleSheet(
            f"color: {_TEXT_DIM}; font-size: 10px; font-style: italic; border: none;"
        )
        right_vbox.addWidget(formula_lbl)

        valider_btn = QPushButton("Valider")
        valider_btn.setFixedHeight(30)
        valider_btn.setStyleSheet(
            f"QPushButton {{ background-color: #1a3a4a; color: #7ab8e0;"
            f" border: 1px solid #7ab8e0; border-radius: 4px;"
            f" font-size: 12px; font-weight: 600; }}"
            f" QPushButton:hover {{ background-color: #1e4a5e; }}"
        )
        valider_btn.clicked.connect(
            lambda: self._on_valider_stock_reel(path, stock_reel_spin)
        )
        right_vbox.addWidget(valider_btn)
        right_vbox.addStretch()

        qty_hbox.addWidget(left_col, 1)
        qty_hbox.addWidget(vsep)
        qty_hbox.addWidget(right_col, 1)

        qty_block.setVisible(has_qty)
        suivi_chk.toggled.connect(qty_block.setVisible)
        lyt.addWidget(qty_block)

        # Stocker les refs pour mise à jour par le timer
        self._detail_fichier_lbl    = fichier_lbl
        self._detail_cache_lbl      = cache_val_lbl
        self._detail_prep_lbl       = prep_val_lbl
        self._detail_stock_reel_lbl = stock_reel_lbl

        lyt.addWidget(self._make_separator())

        # ── Statut (toggle local avant enregistrement) ───────────────────
        status_lbl = QLabel("Statut")
        status_lbl.setStyleSheet(
            f"color: {_TEXT_SECTION}; font-size: 13px; font-weight: 700; border: none;"
        )
        lyt.addWidget(status_lbl)

        status_row = QHBoxLayout()
        status_row.setSpacing(8)

        badge_en_stock = QPushButton("En stock")
        badge_rupture  = QPushButton("Rupture")
        badge_en_stock.setFixedHeight(30)
        badge_rupture.setFixedHeight(30)

        def _apply_status_style():
            if oos_state[0]:
                badge_rupture.setStyleSheet(
                    f"QPushButton {{ background-color: #5e1a1a; color: {_CLR_OOS};"
                    f" border: 1px solid {_CLR_OOS}; border-radius: 4px;"
                    f" font-size: 12px; font-weight: 700; padding: 2px 10px; }}"
                )
                badge_en_stock.setStyleSheet(
                    f"QPushButton {{ background-color: {_TAG_OFF_BG}; color: {_TAG_OFF_FG};"
                    f" border: 1px solid {_TAG_OFF_BD}; border-radius: 4px;"
                    f" font-size: 12px; padding: 2px 10px; }}"
                    f" QPushButton:hover {{ background-color: #444950; }}"
                )
            else:
                badge_en_stock.setStyleSheet(
                    f"QPushButton {{ background-color: #1a5e2a; color: {_CLR_IN_STOCK};"
                    f" border: 1px solid {_CLR_IN_STOCK}; border-radius: 4px;"
                    f" font-size: 12px; font-weight: 700; padding: 2px 10px; }}"
                )
                badge_rupture.setStyleSheet(
                    f"QPushButton {{ background-color: {_TAG_OFF_BG}; color: {_TAG_OFF_FG};"
                    f" border: 1px solid {_TAG_OFF_BD}; border-radius: 4px;"
                    f" font-size: 12px; padding: 2px 10px; }}"
                    f" QPushButton:hover {{ background-color: #444950; }}"
                )

        def _save_oos(new_oos: bool) -> None:
            oos_state[0] = new_oos
            _apply_status_style()
            file_data_oos = get_stock_data()
            node_oos = _resolve_path(file_data_oos, path)
            if isinstance(node_oos, dict):
                node_oos["OutOfStock"] = new_oos
                save_stock_data(file_data_oos)
                cache_oos = get_stock_cache()
                if cache_oos is not None:
                    cache_oos.set_out_of_stock(path, new_oos)
            self.refresh()

        badge_en_stock.clicked.connect(lambda: _save_oos(False))
        badge_rupture.clicked.connect(lambda: _save_oos(True))
        _apply_status_style()

        status_row.addStretch()
        status_row.addWidget(badge_en_stock)
        status_row.addWidget(badge_rupture)
        status_row.addStretch()
        lyt.addLayout(status_row)

        lyt.addStretch()
        lyt.addWidget(self._make_separator())

        # ── Bouton Enregistrer ────────────────────────────────────────────
        save_btn = QPushButton("Enregistrer")
        save_btn.setObjectName("saveButton")
        save_btn.setMinimumHeight(38)
        save_btn.setStyleSheet(
            f"""
            QPushButton#saveButton {{
                background-color: #1a4a2a;
                color: {_CLR_IN_STOCK};
                border: 1px solid {_CLR_IN_STOCK};
                border-radius: 6px;
                font-size: 14px;
                font-weight: 700;
                padding: 6px 20px;
            }}
            QPushButton#saveButton:hover {{ background-color: #1e5e32; }}
            """
        )
        save_btn.clicked.connect(
            lambda: self._on_save_detail(path, cat_combo, name_edit, suivi_chk)
        )
        lyt.addWidget(save_btn)

        self.right_scroll.setWidget(content)
        self._detail_widget = content
        self.right_scroll.setFocus()

    def _update_detail_readonly(
        self,
        file_data: Dict,
        cache_data: Dict,
        by_nom: Dict,
        by_plat: Dict,
    ) -> None:
        """Met à jour les labels lecture seule du détail sans reconstruire le formulaire."""
        if (
            self._selected_path is None
            or self._detail_cache_lbl is None
            or self._detail_fichier_lbl is None
        ):
            return
        path = self._selected_path
        node = _resolve_path(file_data, path)
        if not isinstance(node, dict):
            return
        cache_node   = _resolve_path(cache_data, path) or {}
        cache_qty    = cache_node.get("Quantité")
        prep         = _get_prep_count(path, node, by_nom, by_plat)
        stock_reel   = (cache_qty + prep) if cache_qty is not None else None

        fichier_qty = int(node.get("Quantité", 0) or 0)
        self._detail_fichier_lbl.setText(str(fichier_qty))
        self._detail_cache_lbl.setText("—" if cache_qty is None else str(cache_qty))
        self._detail_prep_lbl.setText(str(prep))
        self._detail_stock_reel_lbl.setText("—" if stock_reel is None else str(stock_reel))

    def _make_separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_BORDER_SECTION}; border: none; border-top: 1px solid {_BORDER_SECTION};")
        return sep

    def _form_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {_TEXT_DIM}; font-size: 12px; border: none;")
        return lbl

    # ── Construction des sections ───────────────────────────────────────────

    def _build_section(
        self,
        section_name: str,
        section_node: Dict[str, Any],
        carte_set: Set[str],
        query: str,
    ) -> Optional[QFrame]:
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 4, 8, 6)
        content_layout.setSpacing(3)

        has_content = self._populate_content(
            content_layout, [section_name], section_node,
            carte_set, query, depth=0,
        )
        if not has_content:
            content_widget.deleteLater()
            return None

        all_leaves: List[Dict] = []
        self._collect_leaves(section_node, all_leaves)
        n_total = len(all_leaves)
        n_oos   = sum(1 for leaf in all_leaves if leaf.get("OutOfStock", False))

        is_expanded = True if query else self._sections_expanded.get(section_name, True)

        section_frame = QFrame()
        section_frame.setObjectName("sectionFrame")
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(0)

        header = self._build_section_header(
            section_name, n_total, n_oos, content_widget, is_expanded, query,
        )
        section_layout.addWidget(header)
        section_layout.addWidget(content_widget)
        content_widget.setVisible(is_expanded)

        section_frame.setStyleSheet(
            f"""
            QFrame#sectionFrame {{
                background-color: {_BG_SECTION};
                border: 1px solid {_BORDER_SECTION};
                border-radius: 6px;
            }}
            """
        )
        return section_frame

    def _build_section_header(
        self,
        name: str,
        n_total: int,
        n_oos: int,
        content_widget: QWidget,
        is_expanded: bool,
        query: str,
    ) -> QFrame:
        header = QFrame()
        header.setObjectName("sectionHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        toggle_btn = QPushButton("▼" if is_expanded else "▶")
        toggle_btn.setFixedSize(20, 20)
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.setStyleSheet(
            f"QPushButton {{ color: {_TEXT_DIM}; background: transparent; border: none; font-size: 11px; }}"
            f"QPushButton:hover {{ color: {_TEXT_TITLE}; }}"
        )

        name_label = QLabel(name)
        name_label.setStyleSheet(
            f"color: {_TEXT_SECTION}; font-size: 14px; font-weight: 700; border: none;"
        )

        oos_text  = f"  ·  {n_oos} rupture{'s' if n_oos > 1 else ''}" if n_oos > 0 else ""
        stats_lbl = QLabel(f"{n_total} article{'s' if n_total > 1 else ''}{oos_text}")
        stats_lbl.setStyleSheet(
            f"color: {_CLR_OOS if n_oos > 0 else _TEXT_DIM}; font-size: 12px; border: none;"
        )

        layout.addWidget(toggle_btn)
        layout.addWidget(name_label)
        layout.addStretch()
        layout.addWidget(stats_lbl)

        if not query:
            toggle_btn.clicked.connect(
                lambda: self._toggle_section(name, content_widget, toggle_btn)
            )

        header.setStyleSheet(
            f"QFrame#sectionHeader {{ background-color: transparent;"
            f" border-bottom: 1px solid {_BORDER_SECTION}; }}"
        )
        return header

    def _toggle_section(self, name: str, content: QWidget, btn: QPushButton) -> None:
        expanded = self._sections_expanded.get(name, True)
        new_state = not expanded
        self._sections_expanded[name] = new_state
        content.setVisible(new_state)
        btn.setText("▼" if new_state else "▶")

    def _collect_leaves(self, node: Any, result: List[Dict]) -> None:
        if not isinstance(node, dict):
            return
        if _is_stock_leaf(node):
            result.append(node)
        else:
            for value in node.values():
                if isinstance(value, dict):
                    self._collect_leaves(value, result)

    def _populate_content(
        self,
        layout: QVBoxLayout,
        path: List[str],
        node: Dict[str, Any],
        carte_set: Set[str],
        query: str,
        depth: int,
    ) -> bool:
        has_content = False
        for key, value in node.items():
            if not isinstance(value, dict):
                continue
            child_path = path + [key]
            if _is_stock_leaf(value):
                if query and not self._matches_search(child_path, value, query):
                    continue
                row = self._build_item_row(child_path, value, carte_set)
                layout.addWidget(row)
                has_content = True
            else:
                sub_container = QWidget()
                sub_layout    = QVBoxLayout(sub_container)
                sub_layout.setContentsMargins(0, 0, 0, 0)
                sub_layout.setSpacing(3)
                sub_has = self._populate_content(
                    sub_layout, child_path, value, carte_set, query, depth + 1,
                )
                if sub_has:
                    layout.addWidget(self._build_subgroup_label(key, depth))
                    layout.addWidget(sub_container)
                    has_content = True
                else:
                    sub_container.deleteLater()
        return has_content

    def _build_subgroup_label(self, name: str, depth: int) -> QLabel:
        indent = 8 * depth
        lbl = QLabel(name)
        lbl.setStyleSheet(
            f"color: {_TEXT_SUBGROUP}; font-size: 12px; font-weight: 600;"
            f" padding: 5px 4px 2px {indent + 4}px;"
            f" border-bottom: 1px solid {_BORDER_ITEM};"
        )
        return lbl

    # ── Ligne d'article ─────────────────────────────────────────────────────

    def _build_item_row(
        self,
        path: List[str],
        node: Dict[str, Any],
        carte_set: Set[str],
    ) -> _ClickableRow:
        out_of_stock = node.get("OutOfStock", False)
        has_qty      = "Quantité" in node
        item_name    = path[-1]
        is_in_carte  = item_name in carte_set
        is_selected  = (path == self._selected_path)

        row = _ClickableRow(path)
        row.setObjectName("stockItemRow")
        h = QHBoxLayout(row)
        h.setContentsMargins(10, 5, 8, 5)
        h.setSpacing(6)
        row.clicked.connect(self._on_item_clicked)

        # Indicateur coloré
        dot = QLabel("●")
        dot.setFixedWidth(12)
        dot.setStyleSheet(
            f"color: {_CLR_OOS if out_of_stock else _CLR_IN_STOCK};"
            f" font-size: 11px; border: none; padding: 0;"
        )
        h.addWidget(dot)

        # Nom
        name_lbl = QLabel(item_name)
        name_lbl.setStyleSheet(
            f"color: {_TEXT_ITEM_OOS if out_of_stock else _TEXT_ITEM};"
            f" font-size: 13px; border: none;"
        )
        h.addWidget(name_lbl, 1)

        # ── Tags alignés à droite (ordre fixe : Carte · Suivi · État) ────
        h.addWidget(self._make_tag(
            "Carte",
            is_in_carte,
            _CLR_CARTE_BG, _CLR_CARTE_BD, _CLR_CARTE_FG,
            _TAG_W_CARTE,
        ))
        h.addWidget(self._make_tag(
            "Suivi",
            has_qty,
            _CLR_SUIVI_BG, _CLR_SUIVI_BD, _CLR_SUIVI_FG,
            _TAG_W_SUIVI,
        ))
        h.addWidget(self._make_etat_tag(out_of_stock))

        # Style de fond selon état et sélection
        if is_selected:
            bg     = _BG_ITEM_SEL
            border = _BORDER_SEL
        elif out_of_stock:
            bg     = _BG_ITEM_OOS
            border = _BORDER_OOS
        else:
            bg     = _BG_ITEM_OK
            border = _BORDER_ITEM

        row.setStyleSheet(
            f"QFrame#stockItemRow {{ background-color: {bg};"
            f" border: 1px solid {border}; border-radius: 4px; }}"
        )
        return row

    def _make_tag(
        self,
        text: str,
        active: bool,
        bg_on: str,
        bd_on: str,
        fg_on: str,
        width: int,
    ) -> QLabel:
        """Crée un tag badge coloré quand actif, grisé quand inactif."""
        tag = QLabel(text)
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag.setFixedWidth(width)
        if active:
            tag.setStyleSheet(
                f"QLabel {{ background-color: {bg_on}; color: {fg_on};"
                f" border: 1px solid {bd_on}; border-radius: 3px;"
                f" font-size: 10px; font-weight: 600; padding: 1px 4px; }}"
            )
        else:
            tag.setStyleSheet(
                f"QLabel {{ background-color: {_TAG_OFF_BG}; color: {_TAG_OFF_FG};"
                f" border: 1px solid {_TAG_OFF_BD}; border-radius: 3px;"
                f" font-size: 10px; padding: 1px 4px; }}"
            )
        return tag

    def _make_etat_tag(self, out_of_stock: bool) -> QLabel:
        """Crée le tag d'état (En stock / Rupture) toujours coloré."""
        tag = QLabel("Rupture" if out_of_stock else "En stock")
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag.setFixedWidth(_TAG_W_ETAT)
        if out_of_stock:
            tag.setStyleSheet(
                f"QLabel {{ background-color: #5e1a1a; color: {_CLR_OOS};"
                f" border: 1px solid {_CLR_OOS}; border-radius: 3px;"
                f" font-size: 10px; font-weight: 600; padding: 1px 4px; }}"
            )
        else:
            tag.setStyleSheet(
                f"QLabel {{ background-color: #1a5e2a; color: {_CLR_IN_STOCK};"
                f" border: 1px solid {_CLR_IN_STOCK}; border-radius: 3px;"
                f" font-size: 10px; font-weight: 600; padding: 1px 4px; }}"
            )
        return tag

    # ── Interactions ────────────────────────────────────────────────────────

    def _on_item_clicked(self, path: List[str]) -> None:
        """Affiche le détail de l'article cliqué dans le panneau droit."""
        self._selected_path = path
        # Reconstruire la liste d'abord pour mettre à jour le highlight
        self.refresh()
        # Charger les données fraîches pour le panneau de détail
        file_data       = get_stock_data()
        cache_obj       = get_stock_cache()
        cache_data      = cache_obj.data if cache_obj is not None else {}
        by_nom, by_plat = _build_prep_data()
        self._build_detail_panel(path, file_data, cache_data, by_nom, by_plat)

    # ── Recherche ──────────────────────────────────────────────────────────

    def _matches_search(self, path: List[str], node: Dict[str, Any], query: str) -> bool:
        text   = " ".join(str(p) for p in path).lower()
        status = "rupture" if node.get("OutOfStock", False) else "en stock"
        return query in text or query in status

    # ── Validation du stock réel ────────────────────────────────────────────

    def _on_valider_stock_reel(self, path: List[str], stock_reel_spin: QSpinBox) -> None:
        """
        Met à jour le fichier et le cache à partir du stock réel saisi manuellement.

        Calcule : fichier (théorique) = stock_réel_saisi − en_préparation
        Met à jour le JSON et le cache en mémoire, puis rafraîchit le panneau.
        """
        stock_reel_saisi = stock_reel_spin.value()

        # Recalculer en préparation au moment du clic (données fraîches)
        file_data       = get_stock_data()
        by_nom, by_plat = _build_prep_data()
        node = _resolve_path(file_data, path)
        if not isinstance(node, dict):
            return

        en_prepa    = _get_prep_count(path, node, by_nom, by_plat)
        new_fichier = max(0, stock_reel_saisi - en_prepa)

        # Mettre à jour le nœud
        node["Quantité"] = new_fichier
        if new_fichier == 0:
            node["OutOfStock"] = True
        elif node.get("OutOfStock", False):
            node["OutOfStock"] = False

        if not save_stock_data(file_data):
            QMessageBox.critical(self, "Stock", "Impossible d'enregistrer le stock.")
            return

        # Mettre à jour le cache en mémoire pour cohérence immédiate
        cache_obj = get_stock_cache()
        if cache_obj is not None:
            cache_obj.set_quantite(path, new_fichier)

        logger.log(logger.MODIFICATION_STOCK_MANUELLE, {
            "action":            "mise_a_jour_stock_reel",
            "chemin":            path,
            "stock_reel_saisi":  stock_reel_saisi,
            "en_prepa":          en_prepa,
            "nouveau_fichier":   new_fichier,
        })

        self._selected_path = path
        self.refresh()
        file_data_fresh = get_stock_data()
        cache_obj       = get_stock_cache()
        cache_data      = cache_obj.data if cache_obj is not None else {}
        by_nom, by_plat = _build_prep_data()
        self._build_detail_panel(path, file_data_fresh, cache_data, by_nom, by_plat)

    # ── Sauvegarde du détail ────────────────────────────────────────────────

    def _on_save_detail(
        self,
        old_path: List[str],
        cat_combo: QComboBox,
        name_edit: QLineEdit,
        suivi_chk: QCheckBox,
    ) -> None:
        new_name    = name_edit.text().strip()
        new_cat_str = cat_combo.currentText().strip()
        suivi_on    = suivi_chk.isChecked()

        if not new_name:
            QMessageBox.warning(self, "Stock", "Le nom ne peut pas être vide.")
            return
        if not new_cat_str:
            QMessageBox.warning(self, "Stock", "Sélectionner une catégorie.")
            return

        file_data = get_stock_data()

        old_node = _resolve_path(file_data, old_path)
        if not isinstance(old_node, dict):
            QMessageBox.warning(self, "Stock", "Article introuvable dans le fichier.")
            return

        # OutOfStock déjà persisté immédiatement via le toggle — on préserve ce qui est dans le fichier
        new_node = dict(old_node)
        if suivi_on:
            if "Quantité" not in new_node:
                new_node["Quantité"] = 0  # suivi activé : initialisation à 0, régler via Valider
        else:
            new_node.pop("Quantité", None)

        new_cat  = [p.strip() for p in new_cat_str.split(" > ")]
        new_path = new_cat + [new_name]

        if new_path != old_path:
            # Vérifier conflit de nom dans la nouvelle catégorie
            existing = _resolve_path(file_data, new_path)
            if existing is not None:
                QMessageBox.warning(
                    self, "Stock",
                    f"Un article « {new_name} » existe déjà dans « {new_cat_str} »."
                )
                return

            # Supprimer l'ancien emplacement
            old_parent = _resolve_path(file_data, old_path[:-1])
            if isinstance(old_parent, dict):
                old_parent.pop(old_path[-1], None)

            # Créer le nouvel emplacement (dicts intermédiaires si besoin)
            target = file_data
            for key in new_cat:
                if key not in target or not isinstance(target[key], dict):
                    target[key] = {}
                target = target[key]
            target[new_name] = new_node
        else:
            # Même chemin : mise à jour sur place
            parent = _resolve_path(file_data, old_path[:-1])
            if isinstance(parent, dict):
                parent[old_path[-1]] = new_node

        if not save_stock_data(file_data):
            QMessageBox.critical(self, "Stock", "Impossible d'enregistrer le stock.")
            return

        logger.log(logger.MODIFICATION_STOCK_MANUELLE, {
            "action": "modification_article",
            "ancien_chemin": old_path,
            "nouveau_chemin": new_path,
            "out_of_stock": new_oos,
        })

        self._selected_path = new_path
        self.refresh()
        # Reconstruire le détail avec les données fraîches
        file_data_fresh = get_stock_data()
        cache_obj       = get_stock_cache()
        cache_data      = cache_obj.data if cache_obj is not None else {}
        by_nom, by_plat = _build_prep_data()
        self._build_detail_panel(new_path, file_data_fresh, cache_data, by_nom, by_plat)
