#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI.py - Vue statistiques

Description:
    Interface Qt/PySide6 de consultation des statistiques de vente : totaux,
    graphiques (répartition par plat, par moyen de paiement, chiffre d'affaires
    par jour), tableaux détaillés, filtrage par période et export du rapport
    en PDF.
    Seules les commandes terminées sont comptabilisées (voir
    src.modules.stats.backend.stats.calculer_statistiques).

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.05

Date de modification:
    2026.07.05
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.utils.tactile import ScrollAreaTactile
from src.UI.utils.icones import icone
from src.backend import logger
from src.backend.data_sources import get_all_history_orders, signature_history_orders
from src.modules.stats.backend.pdf_export import generer_rapport_pdf
from src.modules.stats.backend.stats import (
    calculer_affluence,
    calculer_composition_par_plat,
    calculer_delais_livraison,
    calculer_statistiques,
    calculer_temps_preparation,
)

# ── Couleurs (identiques aux autres modules de consultation) ─────────────────
_BG_MAIN     = "#2f3136"
_BG_CARD     = "#3a3d43"
_BORDER_CARD = "#7f7f7f"
_TEXT_TITLE  = "#f5f5f5"
_TEXT_MUTED  = "#a8acb3"

_PALETTE = [
    "#4a7fcb", "#d4a017", "#4caf50", "#c0392b",
    "#9b59b6", "#c97a30", "#5865f2", "#e05c5c",
]


class StatsModule(QFrame):
    """Module de consultation des statistiques de vente, avec export PDF."""

    go_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statsModule")
        self._stats: Dict[str, Any] = {}
        self._affluence: Dict[str, Any] = {}
        self._temps_preparation: Dict[str, Any] = {}
        self._delais_livraison: Dict[str, Any] = {}
        self._composition: Dict[str, Dict[str, Any]] = {}
        self._last_key: Optional[tuple] = None
        self._build_ui()
        self._build_timer()
        self.refresh()

    # ── Construction de l'interface ─────────────────────────────────────────

    def _build_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(8)

        title = QLabel("Statistiques")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("sectionTitle")
        main_layout.addWidget(title)

        main_layout.addLayout(self._build_filter_row())

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)

        self.general_layout = self._build_onglet_scrollable("Vue générale")
        self.plats_tabs = QTabWidget()
        self.plats_tabs.setDocumentMode(True)
        page_plats = QWidget()
        page_plats_layout = QVBoxLayout(page_plats)
        page_plats_layout.setContentsMargins(0, 0, 0, 0)
        page_plats_layout.addWidget(self.plats_tabs)
        self.tabs.addTab(page_plats, "Par plat")

        main_layout.addLayout(self._build_bottom_bar())

        self.setStyleSheet(
            f"""
            QFrame#statsModule {{
                background-color: {_BG_MAIN};
                border: 1px solid {_BORDER_CARD};
            }}
            QLabel#sectionTitle {{
                color: {_TEXT_TITLE};
                font-size: 22px;
                font-weight: 700;
                padding: 4px;
            }}
            QLabel#subSectionTitle {{
                color: {_TEXT_TITLE};
                font-size: 15px;
                font-weight: 700;
                padding: 2px 0;
            }}
            QLineEdit {{
                background-color: #3b3f46;
                color: {_TEXT_TITLE};
                border: 1px solid #676d79;
                border-radius: 6px;
                padding: 6px 8px;
            }}
            QPushButton {{
                background-color: #4f545e;
                border: 1px solid #7d8390;
                border-radius: 7px;
                color: {_TEXT_TITLE};
                font-size: 14px;
                font-weight: 700;
                min-height: 38px;
                padding: 6px 12px;
            }}
            QPushButton:hover:enabled {{ background-color: #626978; }}
            QPushButton:disabled {{
                background-color: #3b3f46;
                border: 1px solid #4a4e55;
                color: #595d64;
            }}
            QTableWidget {{
                background-color: {_BG_CARD};
                color: {_TEXT_TITLE};
                border: 1px solid {_BORDER_CARD};
                gridline-color: #4a4e55;
            }}
            QHeaderView::section {{
                background-color: #23272a;
                color: {_TEXT_TITLE};
                padding: 4px;
                border: 1px solid {_BORDER_CARD};
                font-weight: 600;
            }}
            QTabWidget::pane {{
                background-color: {_BG_MAIN};
                border: 1px solid {_BORDER_CARD};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {_BG_CARD};
                color: {_TEXT_MUTED};
                border: 1px solid {_BORDER_CARD};
                border-bottom: none;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {_BG_MAIN};
                color: {_TEXT_TITLE};
            }}
            QTabBar::tab:hover {{
                color: {_TEXT_TITLE};
            }}
            """
        )

    def _build_onglet_scrollable(self, titre: str) -> QVBoxLayout:
        """Crée un onglet défilant (scroll area + conteneur) ajouté à self.tabs, et retourne son layout de contenu."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = ScrollAreaTactile(_BG_MAIN)
        page_layout.addWidget(scroll_area)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        scroll_area.setWidget(content_container)

        self.tabs.addTab(page, titre)
        return content_layout

    def _build_page_plat_scrollable(self) -> tuple:
        """Crée une page défilante (scroll area + conteneur) destinée à un onglet de self.plats_tabs.

        :return: tuple (page, content_layout) — le layout est à remplir, la page à ajouter via addTab.
        """
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = ScrollAreaTactile(_BG_CARD)
        page_layout.addWidget(scroll_area)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(12)
        scroll_area.setWidget(content_container)

        return page, content_layout

    def _build_filter_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        label_periode = QLabel("Période :")
        label_periode.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px;")
        row.addWidget(label_periode)

        self.date_from_field = QLineEdit()
        self.date_from_field.setPlaceholderText("JJ/MM/AAAA")
        self.date_from_field.setMaximumWidth(115)
        self.date_from_field.textChanged.connect(self.refresh)
        row.addWidget(self.date_from_field)

        label_a = QLabel("→")
        label_a.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px;")
        row.addWidget(label_a)

        self.date_to_field = QLineEdit()
        self.date_to_field.setPlaceholderText("JJ/MM/AAAA")
        self.date_to_field.setMaximumWidth(115)
        self.date_to_field.textChanged.connect(self.refresh)
        row.addWidget(self.date_to_field)

        reset_btn = QPushButton("Réinitialiser")
        reset_btn.clicked.connect(self._reinitialiser_periode)
        row.addWidget(reset_btn)

        row.addStretch()
        return row

    def _build_bottom_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()

        self.back_button = QPushButton("  Retour")
        self.back_button.setObjectName("backButton")
        self.back_button.setIcon(icone("return.svg", 18))
        self.back_button.setIconSize(QSize(18, 18))
        self.back_button.clicked.connect(self.go_back.emit)
        bar.addWidget(self.back_button)

        bar.addStretch()

        self.export_button = QPushButton("  Exporter en PDF")
        self.export_button.setIcon(icone("save.svg", 18))
        self.export_button.setIconSize(QSize(18, 18))
        self.export_button.clicked.connect(self._on_export_pdf)
        bar.addWidget(self.export_button)

        return bar

    def _build_timer(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start()

    # ── Filtrage par période ─────────────────────────────────────────────────

    def _reinitialiser_periode(self):
        self.date_from_field.clear()
        self.date_to_field.clear()

    def _parse_date(self, texte: str, defaut_heure: str) -> Optional[datetime]:
        texte = texte.strip()
        if not texte:
            return None
        heure, minute = (23, 59) if defaut_heure == "23:59" else (0, 0)
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                d = datetime.strptime(texte, fmt)
                return d.replace(hour=heure, minute=minute)
            except ValueError:
                continue
        return None

    def _titre_periode(self) -> str:
        df = self.date_from_field.text().strip()
        dt = self.date_to_field.text().strip()
        if df and dt:
            return f"Du {df} au {dt}"
        if df:
            return f"Depuis le {df}"
        if dt:
            return f"Jusqu'au {dt}"
        return ""

    # ── Rafraîchissement ─────────────────────────────────────────────────────

    def refresh(self):
        """Recalcule les statistiques si les données ou le filtre ont changé."""
        cle = (
            signature_history_orders(),
            self.date_from_field.text().strip(),
            self.date_to_field.text().strip(),
        )
        if cle == self._last_key:
            return
        self._last_key = cle

        date_from = self._parse_date(self.date_from_field.text(), "00:00")
        date_to = self._parse_date(self.date_to_field.text(), "23:59")
        orders = get_all_history_orders()
        self._stats = calculer_statistiques(orders, date_from, date_to)
        self._affluence = calculer_affluence(orders, date_from, date_to)
        self._temps_preparation = calculer_temps_preparation(orders, date_from, date_to)
        self._delais_livraison = calculer_delais_livraison(orders, date_from, date_to)
        self._composition = calculer_composition_par_plat(orders, date_from, date_to)
        self._render_stats()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_stats(self):
        stats = self._stats
        totaux = stats.get("totaux", {})
        self.export_button.setEnabled(bool(totaux.get("nb_commandes")))

        self._render_vue_generale()
        self._render_par_plat()

    def _render_vue_generale(self):
        self._clear_layout(self.general_layout)
        stats = self._stats
        totaux = stats.get("totaux", {})

        self.general_layout.addWidget(self._build_cartes_row([
            ("Commandes", str(totaux.get("nb_commandes", 0))),
            ("Montant total", f"{totaux.get('montant_total', 0):.2f} €"),
            ("Panier moyen", f"{totaux.get('panier_moyen', 0):.2f} €"),
            ("Plats vendus", str(totaux.get("nb_plats", 0))),
        ]))

        plats = stats.get("plats", [])
        if plats:
            self.general_layout.addWidget(self._build_section_title("Ventilation par plat"))
            top_plats = plats[:8]
            self.general_layout.addWidget(self._build_bar_chart(
                [p["nom"] for p in top_plats], [p["quantite"] for p in top_plats], "Quantité vendue",
            ))

        paiements = stats.get("paiements", [])
        if paiements:
            self.general_layout.addWidget(self._build_section_title("Répartition des moyens de paiement"))
            self.general_layout.addWidget(self._build_pie_chart(
                [p["type"] for p in paiements], [p["quantite"] for p in paiements],
            ))
            self.general_layout.addWidget(self._build_table_paiements(paiements))

        ca_par_jour = stats.get("ca_par_jour", [])
        if len(ca_par_jour) > 1:
            self.general_layout.addWidget(self._build_section_title("Chiffre d'affaires par jour"))
            self.general_layout.addWidget(self._build_bar_chart(
                [j["date"] for j in ca_par_jour], [j["montant"] for j in ca_par_jour], "Montant (€)",
            ))

        affluence = self._affluence.get("par_heure", [])
        totaux_affluence = self._affluence.get("totaux", {})
        if totaux_affluence.get("nb_commandes_validees"):
            self.general_layout.addWidget(self._build_section_title("Horaires d'affluence"))
            note = QLabel(
                f"{totaux_affluence.get('nb_commandes_validees', 0)} commande(s) validée(s) prise(s) en "
                f"compte, dont {totaux_affluence.get('nb_annulees', 0)} annulée(s) (basé sur l'heure de "
                "validation, indépendamment du statut final)."
            )
            note.setWordWrap(True)
            note.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
            self.general_layout.addWidget(note)
            self.general_layout.addWidget(self._build_bar_chart(
                [h["heure"] for h in affluence], [h["quantite"] for h in affluence], "Commandes validées",
            ))

        if not totaux.get("nb_commandes"):
            vide = QLabel("Aucune commande terminée sur cette période.")
            vide.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vide.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 14px; padding: 20px;")
            self.general_layout.addWidget(vide)

        self.general_layout.addStretch()

    def _render_par_plat(self):
        """Reconstruit l'onglet "Par plat" : un sous-onglet par plat présent dans la période,
        avec un contenu plus ou moins riche selon les données disponibles pour ce type de plat
        (recettes pour la pizza, composition pour les plats personnalisables, temps de
        préparation/retrait si mesurés, ou simplement les totaux de vente pour un plat simple).
        """
        onglet_precedent = self.plats_tabs.tabText(self.plats_tabs.currentIndex())

        while self.plats_tabs.count():
            widget = self.plats_tabs.widget(0)
            self.plats_tabs.removeTab(0)
            widget.deleteLater()

        plats = self._stats.get("plats", [])
        temps_prepa_par_plat = {p["plat"]: p for p in self._temps_preparation.get("par_plat", [])}
        delais_par_plat = {p["plat"]: p for p in self._delais_livraison.get("par_plat", [])}

        for info_plat in sorted(plats, key=lambda p: p["nom"]):
            nom = info_plat["nom"]
            page, layout = self._build_page_plat_scrollable()
            self._render_page_plat(
                layout, info_plat,
                temps_prepa_par_plat.get(nom), delais_par_plat.get(nom), self._composition.get(nom),
            )
            self.plats_tabs.addTab(page, nom)

        if not plats:
            page, layout = self._build_page_plat_scrollable()
            vide = QLabel("Aucun plat vendu sur cette période.")
            vide.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vide.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 14px; padding: 20px;")
            layout.addWidget(vide)
            layout.addStretch()
            self.plats_tabs.addTab(page, "—")

        index_restaure = next(
            (i for i in range(self.plats_tabs.count()) if self.plats_tabs.tabText(i) == onglet_precedent), 0,
        )
        self.plats_tabs.setCurrentIndex(index_restaure)

    def _render_page_plat(
        self, layout: QVBoxLayout, info_plat: Dict[str, Any],
        temps_prepa: Optional[Dict[str, Any]], delais: Optional[Dict[str, Any]],
        composition: Optional[Dict[str, Any]],
    ):
        nom = info_plat["nom"]

        layout.addWidget(self._build_cartes_row([
            ("Quantité vendue", str(info_plat["quantite"])),
            ("Montant", f"{info_plat['montant']:.2f} €"),
            ("Prix moyen", f"{info_plat['prix_moyen']:.2f} €"),
        ]))

        if temps_prepa or delais:
            layout.addWidget(self._build_section_title("Délais"))
            cartes_delais = []
            if temps_prepa:
                cartes_delais.append((
                    "Préparation moyenne",
                    f"{temps_prepa['temps_moyen_minutes']:.1f} min",
                ))
            if delais:
                cartes_delais.append((
                    "Retrait moyen",
                    f"{delais['temps_moyen_minutes']:.1f} min",
                ))
            layout.addWidget(self._build_cartes_row(cartes_delais))
            if temps_prepa:
                layout.addWidget(self._build_table_durees([temps_prepa]))
            if delais:
                layout.addWidget(self._build_table_durees([delais]))

        if nom == "Pizza":
            recettes = self._stats.get("recettes_pizza", [])
            if recettes:
                layout.addWidget(self._build_section_title("Recettes les plus vendues"))
                layout.addWidget(self._build_pie_chart(
                    [r["recette"] for r in recettes], [r["quantite"] for r in recettes],
                ))
                layout.addWidget(self._build_table_recettes(recettes))
            if composition:
                self._ajouter_classement(layout, "Ingrédients ajoutés", composition.get("ajouts", []))
                self._ajouter_classement(layout, "Ingrédients retirés", composition.get("retraits", []))

        elif nom == "Grillade" and composition:
            self._ajouter_classement(layout, "Viandes les plus servies", composition.get("viandes", []))
            self._ajouter_classement(layout, "Accompagnements choisis", composition.get("accompagnements", []))

        elif nom == "Crêpe" and composition:
            self._ajouter_classement(layout, "Garnitures les plus demandées", composition.get("garnitures", []))

        elif nom == "Salade composée" and composition:
            self._ajouter_classement(layout, "Ingrédients les plus choisis", composition.get("ingredients", []))

        layout.addStretch()

    def _ajouter_classement(self, layout: QVBoxLayout, titre: str, classement: List[Dict[str, Any]]):
        """Ajoute au layout un titre + tableau de classement {nom, quantite}, si non vide."""
        if not classement:
            return
        layout.addWidget(self._build_section_title(titre))
        lignes = [[c["nom"], self._formater_quantite(c["quantite"])] for c in classement]
        layout.addWidget(self._build_table(["Nom", "Quantité"], lignes))

    def _formater_quantite(self, quantite: float) -> str:
        """Affiche une quantité sans décimale inutile (ex. 1.0 -> "1", 1.5 -> "1.5")."""
        return str(int(quantite)) if float(quantite).is_integer() else f"{quantite:.1f}"

    # ── Construction des blocs d'affichage ──────────────────────────────────

    def _build_section_title(self, texte: str) -> QLabel:
        label = QLabel(texte)
        label.setObjectName("subSectionTitle")
        return label

    def _build_cartes_row(self, cartes: List[tuple]) -> QFrame:
        """Construit une rangée de cartes (libellé, valeur) — totaux généraux ou totaux d'un plat."""
        conteneur = QFrame()
        layout = QHBoxLayout(conteneur)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        for libelle, valeur in cartes:
            carte = QFrame()
            carte.setStyleSheet(
                f"QFrame {{ background-color: {_BG_CARD}; border: 1px solid {_BORDER_CARD}; border-radius: 8px; }}"
            )
            carte_layout = QVBoxLayout(carte)
            carte_layout.setContentsMargins(12, 10, 12, 10)
            valeur_label = QLabel(valeur)
            valeur_label.setStyleSheet(f"color: {_TEXT_TITLE}; font-size: 20px; font-weight: 700;")
            libelle_label = QLabel(libelle)
            libelle_label.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
            carte_layout.addWidget(valeur_label)
            carte_layout.addWidget(libelle_label)
            layout.addWidget(carte)
        return conteneur

    def _style_chart_sombre(self, chart: QChart):
        chart.setBackgroundBrush(QColor(_BG_CARD))
        chart.setBackgroundPen(QColor(_BORDER_CARD))
        chart.legend().setLabelColor(QColor(_TEXT_TITLE))
        for axe in list(chart.axes()):
            axe.setLabelsColor(QColor(_TEXT_TITLE))
            axe.setLinePenColor(QColor(_TEXT_MUTED))
            axe.setGridLineColor(QColor("#4a4e55"))

    def _build_bar_chart(self, categories: List[str], valeurs: List[float], titre_serie: str) -> QChartView:
        bar_set = QBarSet(titre_serie)
        bar_set.append(valeurs)
        bar_set.setColor(QColor(_PALETTE[0]))
        series = QBarSeries()
        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.legend().hide()

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        valeurs_entieres = bool(valeurs) and all(float(v).is_integer() for v in valeurs)
        axis_y.setLabelFormat("%d" if valeurs_entieres else "%.1f")
        max_val = max(valeurs) if valeurs else 0
        # Un palier par unité si la plage est petite (≤ 6), sinon les 5 graduations
        # par défaut de Qt (évite les libellés qui se chevauchent en "...").
        if valeurs_entieres and 0 < max_val <= 6:
            axis_y.setTickCount(int(max_val) + 1)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self._style_chart_sombre(chart)

        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setBackgroundBrush(QColor(_BG_CARD))
        view.setMinimumHeight(240)
        return view

    def _build_pie_chart(self, libelles: List[str], valeurs: List[float]) -> QChartView:
        series = QPieSeries()
        for i, (libelle, valeur) in enumerate(zip(libelles, valeurs)):
            part = series.append(f"{libelle} ({valeur:.0f})", valeur)
            part.setBrush(QColor(_PALETTE[i % len(_PALETTE)]))
            part.setLabelVisible(True)
            part.setLabelColor(QColor(_TEXT_TITLE))

        chart = QChart()
        chart.addSeries(series)
        chart.legend().hide()
        self._style_chart_sombre(chart)

        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setBackgroundBrush(QColor(_BG_CARD))
        view.setMinimumHeight(260)
        return view

    def _build_table(self, entetes: List[str], lignes: List[List[str]]) -> QTableWidget:
        table = QTableWidget(len(lignes), len(entetes))
        table.setHorizontalHeaderLabels(entetes)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, len(entetes)):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        for row, valeurs in enumerate(lignes):
            for col, valeur in enumerate(valeurs):
                item = QTableWidgetItem(valeur)
                if col > 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row, col, item)
        table.setFixedHeight(min(34 * (len(lignes) + 1) + 6, 260))
        return table

    def _build_table_paiements(self, paiements: List[Dict[str, Any]]) -> QTableWidget:
        lignes = [
            [p["type"], str(p["quantite"]), f"{p['pourcentage']:.1f} %", f"{p['montant']:.2f} €"]
            for p in paiements
        ]
        return self._build_table(["Moyen de paiement", "Quantité", "% commandes", "Montant"], lignes)

    def _build_table_recettes(self, recettes: List[Dict[str, Any]]) -> QTableWidget:
        lignes = [
            [r["recette"], str(r["quantite"]), f"{r['pourcentage']:.1f} %"]
            for r in recettes
        ]
        return self._build_table(["Recette pizza", "Quantité", "% pizzas"], lignes)

    def _build_table_durees(self, par_plat: List[Dict[str, Any]]) -> QTableWidget:
        lignes = [
            [
                p["plat"], str(p["nb_plats"]),
                f"{p['temps_moyen_minutes']:.1f} min",
                f"{p['temps_min_minutes']:.1f} min",
                f"{p['temps_max_minutes']:.1f} min",
            ]
            for p in par_plat
        ]
        return self._build_table(["Plat", "Nb plats", "Moyenne", "Minimum", "Maximum"], lignes)

    # ── Export PDF ───────────────────────────────────────────────────────────

    def _on_export_pdf(self):
        nom_defaut = f"rapport_stats_{datetime.now():%Y%m%d_%H%M}.pdf"
        chemin, _ = QFileDialog.getSaveFileName(self, "Exporter le rapport PDF", nom_defaut, "PDF (*.pdf)")
        if not chemin:
            return
        if not chemin.lower().endswith(".pdf"):
            chemin += ".pdf"
        try:
            generer_rapport_pdf(
                self._stats, chemin, self._titre_periode(),
                affluence=self._affluence,
                temps_preparation=self._temps_preparation,
                delais_livraison=self._delais_livraison,
            )
        except Exception as e:
            QMessageBox.warning(self, "Export PDF", f"Erreur lors de la génération du PDF :\n{e}")
            return

        logger.log(logger.EXPORT_RAPPORT_STATS, {
            "chemin": chemin,
            "periode": self._titre_periode() or "toutes périodes",
            "nb_commandes": self._stats.get("totaux", {}).get("nb_commandes", 0),
        })
        QMessageBox.information(self, "Export PDF", f"Rapport exporté :\n{Path(chemin).name}")
