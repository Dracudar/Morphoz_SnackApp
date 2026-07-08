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

        self.scroll_area = ScrollAreaTactile(_BG_MAIN)
        main_layout.addWidget(self.scroll_area, 1)

        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        self.scroll_area.setWidget(self.content_container)

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
            """
        )

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
        self._render_stats()

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_stats(self):
        self._clear_content()
        stats = self._stats
        totaux = stats.get("totaux", {})

        self.export_button.setEnabled(bool(totaux.get("nb_commandes")))

        self.content_layout.addWidget(self._build_totaux_row(totaux))

        plats = stats.get("plats", [])
        if plats:
            self.content_layout.addWidget(self._build_section_title("Ventilation par plat"))
            top_plats = plats[:8]
            self.content_layout.addWidget(self._build_bar_chart(
                [p["nom"] for p in top_plats], [p["quantite"] for p in top_plats], "Quantité vendue",
            ))
            self.content_layout.addWidget(self._build_table_plats(plats))

        paiements = stats.get("paiements", [])
        if paiements:
            self.content_layout.addWidget(self._build_section_title("Répartition des moyens de paiement"))
            self.content_layout.addWidget(self._build_pie_chart(
                [p["type"] for p in paiements], [p["quantite"] for p in paiements],
            ))
            self.content_layout.addWidget(self._build_table_paiements(paiements))

        recettes = stats.get("recettes_pizza", [])
        if recettes:
            self.content_layout.addWidget(self._build_section_title("Recettes pizza les plus vendues"))
            self.content_layout.addWidget(self._build_pie_chart(
                [r["recette"] for r in recettes], [r["quantite"] for r in recettes],
            ))
            self.content_layout.addWidget(self._build_table_recettes(recettes))

        ca_par_jour = stats.get("ca_par_jour", [])
        if len(ca_par_jour) > 1:
            self.content_layout.addWidget(self._build_section_title("Chiffre d'affaires par jour"))
            self.content_layout.addWidget(self._build_bar_chart(
                [j["date"] for j in ca_par_jour], [j["montant"] for j in ca_par_jour], "Montant (€)",
            ))

        affluence = self._affluence.get("par_heure", [])
        totaux_affluence = self._affluence.get("totaux", {})
        if totaux_affluence.get("nb_commandes_validees"):
            self.content_layout.addWidget(self._build_section_title("Horaires d'affluence"))
            note = QLabel(
                f"{totaux_affluence.get('nb_commandes_validees', 0)} commande(s) validée(s) prise(s) en "
                f"compte, dont {totaux_affluence.get('nb_annulees', 0)} annulée(s) (basé sur l'heure de "
                "validation, indépendamment du statut final)."
            )
            note.setWordWrap(True)
            note.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
            self.content_layout.addWidget(note)
            self.content_layout.addWidget(self._build_bar_chart(
                [h["heure"] for h in affluence], [h["quantite"] for h in affluence], "Commandes validées",
            ))

        temps_prepa = self._temps_preparation.get("par_plat", [])
        if temps_prepa:
            self.content_layout.addWidget(self._build_section_title("Temps de préparation par type de plat"))
            self.content_layout.addWidget(self._build_bar_chart(
                [p["plat"] for p in temps_prepa], [p["temps_moyen_minutes"] for p in temps_prepa],
                "Temps moyen (min)",
            ))
            self.content_layout.addWidget(self._build_table_durees(temps_prepa))

        delais_livraison = self._delais_livraison.get("par_plat", [])
        if delais_livraison:
            self.content_layout.addWidget(self._build_section_title("Délai de retrait (plat prêt → remis au client)"))
            self.content_layout.addWidget(self._build_bar_chart(
                [p["plat"] for p in delais_livraison], [p["temps_moyen_minutes"] for p in delais_livraison],
                "Délai moyen (min)",
            ))
            self.content_layout.addWidget(self._build_table_durees(delais_livraison))

        if not totaux.get("nb_commandes"):
            vide = QLabel("Aucune commande terminée sur cette période.")
            vide.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vide.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 14px; padding: 20px;")
            self.content_layout.addWidget(vide)

        self.content_layout.addStretch()

    # ── Construction des blocs d'affichage ──────────────────────────────────

    def _build_section_title(self, texte: str) -> QLabel:
        label = QLabel(texte)
        label.setObjectName("subSectionTitle")
        return label

    def _build_totaux_row(self, totaux: Dict[str, Any]) -> QFrame:
        cartes = [
            ("Commandes", str(totaux.get("nb_commandes", 0))),
            ("Montant total", f"{totaux.get('montant_total', 0):.2f} €"),
            ("Panier moyen", f"{totaux.get('panier_moyen', 0):.2f} €"),
            ("Plats vendus", str(totaux.get("nb_plats", 0))),
        ]
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

    def _build_table_plats(self, plats: List[Dict[str, Any]]) -> QTableWidget:
        lignes = [
            [p["nom"], str(p["quantite"]), f"{p['prix_moyen']:.2f} €", f"{p['montant']:.2f} €"]
            for p in plats
        ]
        return self._build_table(["Plat", "Quantité", "Prix moyen", "Montant"], lignes)

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
