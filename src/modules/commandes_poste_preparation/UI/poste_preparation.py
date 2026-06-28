#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
poste_preparation.py - Module du poste de préparation

Description:
    Affichage plein écran des plats en cours de préparation, filtrable par type
    (Pizza, Grillade, Frites, Salade composée, Crêpe). Les plats sont affichés
    en grille (3 colonnes) adaptée aux écrans tactiles 10".

Author :
    Dracudar

Version:
    2.1

Date de création :
    2026.06.08

Date de modification:
    2026.06.13
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.utils.tactile import ScrollAreaTactile
from src.backend.data_sources import get_live_orders_prep, get_types_carte_actifs, signature_live_orders
from src.modules.commandes_poste_preparation.UI.widgets.carte_plat import CartePlatWidget

_COLUMNS = 4  # colonnes en grille (adapté à l'écran 10")

# ── Palette ───────────────────────────────────────────────────────────────────
_BG           = "#2f3136"
_TEXT_TITRE   = "#f5f5f5"
_BTN_INACTIF  = ("background-color: #3a3d43; color: #d6d6d6; border: 1px solid #60646c; "
                 "border-radius: 4px; padding: 5px 14px;")
_BTN_INACTIF_HOVER = "background-color: #4a4e55;"
_BTN_ACTIF    = ("background-color: #4a7fcb; color: #ffffff; border: 1px solid #4a7fcb; "
                 "border-radius: 4px; padding: 5px 14px; font-weight: 700;")
_BTN_ACTIF_HOVER = "background-color: #5a8fdb;"


class PostePreparationModule(QFrame):
    """Page plein écran du poste de préparation (grille 3 colonnes)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("postePreparation")
        self._active_filters: set[str] = set()
        self._filter_buttons: dict[str, QPushButton] = {}
        # État du rafraîchissement incrémental
        self._last_key = None                  # (signature dossier, filtres) au dernier refresh
        self._cards: dict[tuple, CartePlatWidget] = {}   # carte par (order_id, plat id)
        self._card_sigs: dict[tuple, tuple] = {}         # empreinte des données rendues
        self._displayed_order: list[tuple] = []          # ordre des cartes affichées
        self._build_ui()
        self._build_timer()
        self.refresh()

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        main_layout.addLayout(self._build_header())

        self._scroll = ScrollAreaTactile(_BG)

        # Contenu scrollable : grille + stretch pour coller en haut
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(10)
        for col in range(_COLUMNS):
            self._grid_layout.setColumnStretch(col, 1)

        content_layout.addWidget(self._grid_container)
        content_layout.addStretch(1)

        self._scroll.setWidget(scroll_content)
        main_layout.addWidget(self._scroll)

        self.setStyleSheet(f"QFrame#postePreparation {{ background-color: {_BG}; }}")

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(8)

        self._title_label = QLabel("Poste de préparation")
        self._title_label.setStyleSheet(
            f"color: {_TEXT_TITRE}; font-size: 19px; font-weight: 700;"
        )
        header.addWidget(self._title_label, 1)

        self._filter_area_layout = QHBoxLayout()
        self._filter_area_layout.setSpacing(8)
        self._build_filter_buttons()
        header.addLayout(self._filter_area_layout)

        return header

    def _build_filter_buttons(self):
        """Initialise les boutons filtre depuis la carte active (hors Archivé)."""
        for plat_type in get_types_carte_actifs():
            self._ensure_filter_button(plat_type)

    def _ensure_filter_button(self, plat_type: str):
        """Ajoute un bouton filtre pour ce type s'il n'en existe pas déjà un.

        Les boutons ne sont jamais supprimés pendant la session : ils ne peuvent
        qu'apparaître, garantissant la stabilité en plein service.
        """
        if plat_type in self._filter_buttons:
            return
        btn = QPushButton(plat_type)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        active = plat_type in self._active_filters
        btn.setChecked(active)
        btn.toggled.connect(lambda checked, t=plat_type: self._on_filter_toggled(t, checked))
        self._apply_btn_style(btn, active=active)
        self._filter_area_layout.addWidget(btn)
        self._filter_buttons[plat_type] = btn

    def _build_timer(self):
        self._timer = QTimer(self)
        self._timer.setInterval(3000)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    # ── Filtres ───────────────────────────────────────────────────────────────

    def _on_filter_toggled(self, plat_type: str, checked: bool):
        if checked:
            self._active_filters.add(plat_type)
        else:
            self._active_filters.discard(plat_type)
        self._apply_btn_style(self._filter_buttons[plat_type], active=checked)
        self.refresh()

    def _apply_btn_style(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet(
                f"QPushButton {{ {_BTN_ACTIF} }}"
                f"QPushButton:hover {{ {_BTN_ACTIF_HOVER} }}"
            )
        else:
            btn.setStyleSheet(
                f"QPushButton {{ {_BTN_INACTIF} }}"
                f"QPushButton:hover {{ {_BTN_INACTIF_HOVER} }}"
            )

    # ── Données ───────────────────────────────────────────────────────────────

    @staticmethod
    def _plat_signature(plat: dict) -> tuple:
        """Empreinte des données d'un plat effectivement rendues dans sa carte."""
        return (
            plat.get("id", ""),
            plat.get("nom", ""),
            plat.get("plat", ""),
            plat.get("status", ""),
            bool(plat.get("prioritaire", False)),
            repr(plat.get("composition", {})),
        )

    def refresh(self):
        """Rafraîchit la grille : court-circuit si rien n'a changé, sinon diff des seules cartes modifiées."""
        if not self.isVisible():
            return

        # Couche 2 — court-circuit : la clé combine l'état du dossier ET les filtres
        # actifs (un changement de filtre ne modifie pas le mtime mais doit rafraîchir).
        cle = (signature_live_orders(), frozenset(self._active_filters))
        if cle == self._last_key:
            return
        self._last_key = cle

        tous_plats = get_live_orders_prep()

        # Ajouter un bouton pour chaque type découvert dans les commandes en cours
        # (couvre les types absents de la carte, ex. anciens plats archivés toujours en préparation)
        for p in tous_plats:
            if p.get("plat"):
                self._ensure_filter_button(p["plat"])

        if self._active_filters:
            plats = [p for p in tous_plats if p["plat"] in self._active_filters]
        else:
            plats = tous_plats

        # Prioritaires en tête, puis ordre naturel (ID croissant)
        plats.sort(key=lambda p: (0 if p.get("prioritaire") else 1, p["id"]))

        count = len(plats)
        plat_word = "plat" if count <= 1 else "plats"
        self._title_label.setText(
            f"Poste de préparation  —  {count} {plat_word} en cours"
        )

        # Couche 3 — diff : ne reconstruire que les cartes ajoutées ou modifiées.
        nouvelles_cles = [(p.get("order_id", ""), p.get("id", "")) for p in plats]
        nouvel_ensemble = set(nouvelles_cles)

        # Suppressions : plats qui ne sont plus à préparer (livrés, annulés, finalisés).
        for cle_carte in list(self._cards.keys()):
            if cle_carte not in nouvel_ensemble:
                ancienne = self._cards.pop(cle_carte)
                self._grid_layout.removeWidget(ancienne)
                ancienne.deleteLater()
                self._card_sigs.pop(cle_carte, None)

        # Ajouts et modifications.
        for plat, cle_carte in zip(plats, nouvelles_cles):
            sig = self._plat_signature(plat)
            if cle_carte not in self._cards:
                self._cards[cle_carte] = CartePlatWidget(plat, self._on_state_changed, self._scroll)
                self._card_sigs[cle_carte] = sig
            elif sig != self._card_sigs.get(cle_carte):
                ancienne = self._cards[cle_carte]
                self._grid_layout.removeWidget(ancienne)
                ancienne.deleteLater()
                self._cards[cle_carte] = CartePlatWidget(plat, self._on_state_changed, self._scroll)
                self._card_sigs[cle_carte] = sig
            # sinon : carte inchangée, conservée telle quelle.

        # Positionnement dans la grille (positions absolues). Si l'ordre est inchangé
        # (ex. simple changement de statut), seules les cartes reconstruites — retirées
        # de la grille plus haut — sont à replacer. Sinon, on replace toute la séquence
        # (déplacement de widgets, sans reconstruction).
        if nouvelles_cles == self._displayed_order:
            for i, cle_carte in enumerate(nouvelles_cles):
                card = self._cards[cle_carte]
                if self._grid_layout.indexOf(card) == -1:
                    row, col = divmod(i, _COLUMNS)
                    self._grid_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)
        else:
            for card in self._cards.values():
                if self._grid_layout.indexOf(card) != -1:
                    self._grid_layout.removeWidget(card)
            for i, cle_carte in enumerate(nouvelles_cles):
                row, col = divmod(i, _COLUMNS)
                self._grid_layout.addWidget(self._cards[cle_carte], row, col, Qt.AlignmentFlag.AlignTop)
            self._displayed_order = nouvelles_cles

    def _on_state_changed(self, _context=None):
        """Rappelé par le backend après un changement de statut."""
        self.refresh()
