#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vue_liste.py

Description:
    Construction du panneau gauche du module Stock : sections pliables par
    famille, sous-groupes, lignes d'article avec tags (Carte / Suivi / État)
    et logique de recherche libre.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.16

Date de modification:
    2026.06.16
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.backend.data.stock import get_stock_cache, get_stock_data
from src.UI.stock.utilitaires import (
    _BG_ITEM_OK,
    _BG_ITEM_OOS,
    _BG_ITEM_SEL,
    _BG_SECTION,
    _BORDER_ITEM,
    _BORDER_OOS,
    _BORDER_SECTION,
    _BORDER_SEL,
    _build_prep_data,
    _CLR_CARTE_BD,
    _CLR_CARTE_BG,
    _CLR_CARTE_FG,
    _CLR_IN_STOCK,
    _CLR_OOS,
    _CLR_SUIVI_BD,
    _CLR_SUIVI_BG,
    _CLR_SUIVI_FG,
    _is_stock_leaf,
    _TAG_OFF_BD,
    _TAG_OFF_BG,
    _TAG_OFF_FG,
    _TAG_W_CARTE,
    _TAG_W_ETAT,
    _TAG_W_SUIVI,
    _TEXT_DIM,
    _TEXT_ITEM,
    _TEXT_ITEM_OOS,
    _TEXT_SECTION,
    _TEXT_SUBGROUP,
    _TEXT_TITLE,
)


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


# ── Mixin de construction de la liste ───────────────────────────────────────

class _VueListeMixin:
    """Méthodes de construction du panneau liste, mélangées dans StockModule."""

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
                sub_frame = QFrame()
                sub_frame.setObjectName("subgroupFrame")
                sub_frame_lyt = QVBoxLayout(sub_frame)
                sub_frame_lyt.setContentsMargins(6, 0, 6, 6)
                sub_frame_lyt.setSpacing(3)
                sub_frame_lyt.addWidget(self._build_subgroup_label(key))

                items_widget = QWidget()
                items_layout = QVBoxLayout(items_widget)
                items_layout.setContentsMargins(0, 0, 0, 0)
                items_layout.setSpacing(3)
                sub_has = self._populate_content(
                    items_layout, child_path, value, carte_set, query, depth + 1,
                )
                if sub_has:
                    sub_frame_lyt.addWidget(items_widget)
                    layout.addWidget(sub_frame)
                    has_content = True
                else:
                    sub_frame.deleteLater()
        return has_content

    def _build_subgroup_label(self, name: str) -> QLabel:
        lbl = QLabel(name)
        lbl.setStyleSheet(
            f"color: {_TEXT_SUBGROUP}; font-size: 12px; font-weight: 600;"
            f" padding: 6px 4px 4px 6px;"
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
