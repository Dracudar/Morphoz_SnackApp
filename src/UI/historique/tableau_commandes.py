#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tableau_commandes.py

Description:
    Construction des cartes de commande et sous-cartes plat affichées dans
    la liste de l'historique : en-tête dépliable, panneau de synthèse,
    badges de statut commande/plat et icône d'annulation.

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

from typing import Any, Dict

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.utils.tactile import EnTeteCliquable
from src.backend.config.impression import get_print_options

# ── Styles des boutons d'action dans les sous-cartes plat ───────────────────
_STYLE_BTN_PRET = (
    "QPushButton { background-color: #4a3a00; color: #d4a017; border: 1px solid #d4a017;"
    " border-radius: 3px; font-size: 11px; font-weight: 600; padding: 2px 6px; min-height: 22px; }"
    " QPushButton:hover { background-color: #5a4a10; }"
)
_STYLE_BTN_LIVRE = (
    "QPushButton { background-color: #1a4a2a; color: #4caf50; border: 1px solid #4caf50;"
    " border-radius: 3px; font-size: 11px; font-weight: 600; padding: 2px 6px; min-height: 22px; }"
    " QPushButton:hover { background-color: #2a6a3a; }"
)
_STYLE_BTN_ANNULER_PLAT = (
    "QPushButton { background-color: #d9534f; border: 1px solid #ac2925;"
    " border-radius: 4px; padding: 2px 4px; min-width: 24px; min-height: 22px; }"
    " QPushButton:hover:enabled { background-color: #c9302c; }"
    " QPushButton:disabled { background-color: #3b3f46; border: 1px solid #4a4e55; }"
)
_STYLE_BTN_CANCEL_CMD = (
    "QPushButton { background-color: #d9534f; border: 1px solid #ac2925;"
    " border-radius: 4px; padding: 2px 4px; min-width: 26px; min-height: 26px; }"
    " QPushButton:hover:enabled { background-color: #c9302c; }"
    " QPushButton:disabled { background-color: #3b3f46; border: 1px solid #4a4e55; }"
)
_STYLE_BTN_PRINT = (
    "QPushButton { background-color: #3d5068; border: 1px solid #5a80a8; border-radius: 4px;"
    " padding: 2px 4px; min-width: 26px; min-height: 26px; }"
    " QPushButton:hover:enabled { background-color: #4a6a90; }"
    " QPushButton:disabled { background-color: #3b3f46; border: 1px solid #4a4e55; }"
)


def _make_cancel_icon(size: int = 14) -> QIcon:
    """Crée un QIcon cancel.svg colorisé blanc (normal) et gris (désactivé)."""
    def _colorize(color: str) -> QPixmap:
        renderer = QSvgRenderer("assets/icons/cancel.svg")
        raw = QPixmap(size, size)
        raw.fill(Qt.GlobalColor.transparent)
        painter = QPainter(raw)
        renderer.render(painter)
        painter.end()
        result = QPixmap(size, size)
        result.fill(Qt.GlobalColor.transparent)
        p2 = QPainter(result)
        p2.drawPixmap(0, 0, raw)
        p2.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p2.fillRect(result.rect(), QColor(color))
        p2.end()
        return result

    icon = QIcon()
    icon.addPixmap(_colorize("white"), QIcon.Mode.Normal)
    icon.addPixmap(_colorize("#595d64"), QIcon.Mode.Disabled)
    return icon

# ── Couleurs (identiques à conteneur_suivi_commande) ─────────────────────────
_BG_MAIN       = "#2f3136"
_BG_CARD       = "#3a3d43"
_BG_PLAT       = "#4a4e55"
_BORDER_CARD   = "#7f7f7f"
_BORDER_PLAT   = "#60646c"
_TEXT_TITLE    = "#f5f5f5"
_TEXT_CARD_ID  = "#f5f5f5"
_TEXT_CARD_CNT = "#a8acb3"
_TEXT_PLAT     = "#d6d6d6"

# ── Badges statut plat ───────────────────────────────────────────────────────
_STATUTS_PLAT: Dict[str, tuple] = {
    "en préparation": ("#7a4a1a", "#c97a30", "En prép."),
    "prêt":           ("#5e4a00", "#d4a017", "Prêt"),
    "livré":          ("#1a5e2a", "#4caf50", "Livré"),
    "annulé":         ("#5e1a1a", "#c0392b", "Annulé"),
    "non livré":      ("#3d1a5e", "#9b59b6", "Non livré"),
}

# ── Badges statut commande ───────────────────────────────────────────────────
_STATUTS_COMMANDE: Dict[str, tuple] = {
    "validée":  ("#7a4a1a", "#c97a30", "En cours"),
    "terminée": ("#1a5e2a", "#4caf50", "Terminée"),
    "annulée":  ("#5e1a1a", "#c0392b", "Annulée"),
}


class _TableauCommandesMixin:
    """Méthodes de construction des cartes commande/plat, mélangées dans CommandesHistoriqueModule."""

    # ── Construction des cartes ─────────────────────────────────────────────

    def _add_order_card(self, order: Dict[str, Any]):
        order_id = order.get("id", "")
        is_collapsed = order_id not in self._expanded_orders

        card = QFrame()
        card.setObjectName("commandeCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(6)

        # Contenu dépliable : panneau d'infos + sous-cartes plats
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)

        content_layout.addWidget(self._build_order_info_panel(order))
        for item in order.get("items", []):
            content_layout.addWidget(self._build_plat_subcard(item, order))

        card_layout.addWidget(self._build_card_header(order, content_container, is_collapsed))
        card_layout.addWidget(content_container)
        content_container.setVisible(not is_collapsed)

        card.setStyleSheet(
            f"""
            QFrame#commandeCard {{
                background-color: {_BG_CARD};
                border: 1px solid {_BORDER_CARD};
                border-radius: 8px;
            }}
            """
        )

        self.list_layout.insertWidget(self.list_layout.count() - 1, card)

    def _build_card_header(
        self, order: Dict[str, Any], content_container: QWidget, is_collapsed: bool
    ) -> EnTeteCliquable:
        header = EnTeteCliquable()
        header.setObjectName("commandeCardHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        order_id = order.get("id", "")

        toggle_btn = QPushButton("▶" if is_collapsed else "▼")
        toggle_btn.setFixedSize(20, 20)
        toggle_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        toggle_btn.setStyleSheet(
            f"QPushButton {{ color: {_TEXT_CARD_CNT}; background: transparent; border: none; font-size: 11px; }}"
        )
        header_layout.addWidget(toggle_btn)

        header.clicked.connect(lambda: self._toggle_order(order_id, content_container, toggle_btn))

        priority_slot = QLabel("!" if order.get("priority", False) else "")
        priority_slot.setFixedWidth(16)
        priority_slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        priority_slot.setStyleSheet(
            "color: #e74c3c; font-size: 16px; font-weight: 900; padding: 0;"
        )
        header_layout.addWidget(priority_slot)

        id_label = QLabel(order_id)
        id_label.setStyleSheet(f"color: {_TEXT_CARD_ID}; font-size: 14px; font-weight: 700;")
        header_layout.addWidget(id_label)

        header_layout.addStretch()

        header_layout.addWidget(self._build_order_status_badge(order.get("status", "")))

        # Bouton annulation commande (avant le bouton impression)
        order_status = (order.get("status") or "").lower()
        btn_cancel_cmd = QPushButton()
        btn_cancel_cmd.setIcon(_make_cancel_icon(14))
        btn_cancel_cmd.setIconSize(QSize(14, 14))
        btn_cancel_cmd.setToolTip("Annuler la commande")
        btn_cancel_cmd.setEnabled(order_status == "validée")
        btn_cancel_cmd.setStyleSheet(_STYLE_BTN_CANCEL_CMD)
        btn_cancel_cmd.clicked.connect(lambda _, o=order: self._on_annuler_commande(o))
        header_layout.addWidget(btn_cancel_cmd)

        # Bouton impression ticket récap (le plus à droite, désactivé si impression globalement off)
        options = get_print_options()
        btn_recap = QPushButton()
        btn_recap.setIcon(QIcon("assets/icons/print.svg"))
        btn_recap.setIconSize(QSize(14, 14))
        btn_recap.setToolTip("Réimprimer ticket récap" if options["impression_active"] else "Impression désactivée")
        btn_recap.setEnabled(options["impression_active"])
        btn_recap.setStyleSheet(_STYLE_BTN_PRINT)
        btn_recap.clicked.connect(lambda _, o=order: self._on_print_recap(o))
        header_layout.addWidget(btn_recap)

        return header

    def _toggle_order(self, order_id: str, content_container: QWidget, toggle_btn: QPushButton):
        if order_id in self._expanded_orders:
            self._expanded_orders.discard(order_id)
            content_container.setVisible(False)
            toggle_btn.setText("▶")
        else:
            self._expanded_orders.add(order_id)
            content_container.setVisible(True)
            toggle_btn.setText("▼")

    def _build_order_info_panel(self, order: Dict[str, Any]) -> QFrame:
        """Panneau de synthèse affiché en haut du bloc déplié."""
        panel = QFrame()
        panel.setObjectName("orderInfoPanel")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        status = (order.get("status") or "").lower()
        nb_plats = len(order.get("items", []))
        amount = order.get("amount")
        payment = order.get("payment_type") or ""
        created = self._format_date(order.get("created_at", ["", ""]))
        delivery = self._format_date(order.get("finalization_at", ["", ""]))
        cancelled = self._format_date(order.get("cancelled_at", ["", ""]))

        infos = [
            ("Plats", str(nb_plats)),
            ("Montant", f"{amount:.2f} €" if isinstance(amount, (int, float)) else "-"),
        ]
        if payment:
            infos.append(("Paiement", payment))
        if created:
            infos.append(("Créé", created))
        if status == "terminée" and delivery:
            infos.append(("Finalisé", delivery))
        if status == "annulée" and cancelled:
            infos.append(("Annulé", cancelled))

        for i, (key, value) in enumerate(infos):
            if i > 0:
                sep = QLabel("·")
                sep.setStyleSheet(f"color: {_BORDER_PLAT}; font-size: 13px; padding: 0 10px;")
                layout.addWidget(sep)
            key_w = QLabel(f"{key} :")
            key_w.setStyleSheet(f"color: {_TEXT_CARD_CNT}; font-size: 12px;")
            val_w = QLabel(value)
            val_w.setStyleSheet(
                f"color: {_TEXT_PLAT}; font-size: 12px; font-weight: 600; margin-left: 4px;"
            )
            layout.addWidget(key_w)
            layout.addWidget(val_w)

        layout.addStretch()

        panel.setStyleSheet(
            f"""
            QFrame#orderInfoPanel {{
                background-color: #353840;
                border: 1px solid {_BORDER_PLAT};
                border-radius: 4px;
            }}
            """
        )
        return panel

    def _build_plat_subcard(self, item: Dict[str, Any], order: Dict[str, Any]) -> QFrame:
        order_status = (order.get("status") or "").lower()
        item_status = (item.get("status") or "").lower()
        is_active_order = order_status == "validée"
        is_terminal_item = item_status in ("livré", "annulé")
        show_pret = is_active_order and item_status == "en préparation"
        show_livre = is_active_order and item_status in ("en préparation", "prêt")

        options = get_print_options()
        print_enabled = options["impression_active"] and not is_terminal_item

        subcard = QFrame()
        subcard.setObjectName("platSubCard")
        outer_layout = QVBoxLayout(subcard)
        outer_layout.setContentsMargins(8, 4, 8, 4)
        outer_layout.setSpacing(0)

        # ── Ligne : ID, Nom, Badge, boutons d'action, impression (le plus à droite) ──
        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(6)

        full_id = item.get("id", "")
        plat_id_reduit = full_id.rsplit("-", 1)[-1] if "-" in full_id else full_id
        id_label = QLabel(plat_id_reduit)
        id_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 13px; font-weight: 500;")
        main_row.addWidget(id_label)

        nom = item.get("nom") or item.get("plat") or ""
        if nom:
            nom_label = QLabel(nom)
            nom_label.setStyleSheet(f"color: {_TEXT_PLAT}; font-size: 12px;")
            main_row.addWidget(nom_label, 1)
        else:
            main_row.addStretch(1)

        # Badge statut (à gauche des boutons)
        main_row.addWidget(self._build_plat_status_badge(item.get("status", "")))

        # Boutons de changement de statut
        if show_pret:
            btn_pret = QPushButton("→ Prêt")
            btn_pret.setStyleSheet(_STYLE_BTN_PRET)
            btn_pret.setToolTip("Passer ce plat au statut Prêt")
            btn_pret.clicked.connect(lambda _, o=order, i=item: self._on_marquer_pret(o, i))
            main_row.addWidget(btn_pret)

        if show_livre:
            btn_livre = QPushButton("→ Livré")
            btn_livre.setStyleSheet(_STYLE_BTN_LIVRE)
            btn_livre.setToolTip("Passer ce plat au statut Livré")
            btn_livre.clicked.connect(lambda _, o=order, i=item: self._on_marquer_livre(o, i))
            main_row.addWidget(btn_livre)

        # Bouton annulation plat (toujours affiché pour commandes validées, désactivé si terminal)
        if is_active_order:
            btn_annuler = QPushButton()
            btn_annuler.setIcon(_make_cancel_icon(12))
            btn_annuler.setIconSize(QSize(12, 12))
            btn_annuler.setToolTip("Annuler ce plat")
            btn_annuler.setEnabled(not is_terminal_item)
            btn_annuler.setStyleSheet(_STYLE_BTN_ANNULER_PLAT)
            btn_annuler.clicked.connect(lambda _, o=order, i=item: self._on_annuler_plat(o, i))
            main_row.addWidget(btn_annuler)

        # Bouton impression cuisine (le plus à droite, désactivé si terminal ou impression off)
        btn_print = QPushButton()
        btn_print.setIcon(QIcon("assets/icons/print.svg"))
        btn_print.setIconSize(QSize(12, 12))
        btn_print.setToolTip(
            "Réimprimer ticket cuisine pour ce plat" if print_enabled else "Impression désactivée"
        )
        btn_print.setEnabled(print_enabled)
        btn_print.setStyleSheet(_STYLE_BTN_PRINT)
        btn_print.clicked.connect(lambda _, o=order, i=item: self._on_print_cuisine_plat(o, i))
        main_row.addWidget(btn_print)

        outer_layout.addLayout(main_row)

        subcard.setStyleSheet(
            f"""
            QFrame#platSubCard {{
                background-color: {_BG_PLAT};
                border: 1px solid {_BORDER_PLAT};
                border-radius: 4px;
            }}
            """
        )
        return subcard

    def _build_plat_status_badge(self, status: str) -> QLabel:
        key = status.lower()
        bg, fg, label_text = _STATUTS_PLAT.get(key, ("#3a3d43", "#7a7f87", status or "?"))
        badge = QLabel(label_text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {fg};
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
                padding: 1px 6px;
            }}
            """
        )
        return badge

    def _build_order_status_badge(self, status: str) -> QLabel:
        key = status.lower()
        bg, fg, label_text = _STATUTS_COMMANDE.get(key, ("#3a3d43", "#7a7f87", status or "?"))
        badge = QLabel(label_text)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {fg};
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
                padding: 1px 8px;
            }}
            """
        )
        return badge

    def _format_date(self, value: Any) -> str:
        if isinstance(value, list) and len(value) >= 2:
            return f"{value[0]} {value[1]}".strip()
        if isinstance(value, str):
            return value
        return "-"
