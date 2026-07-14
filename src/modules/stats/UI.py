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

    Propose également un rapprochement des paiements carte de l'app avec un
    relevé de ventes CSV exporté depuis SumUp (voir
    src.modules.stats.backend.sumup).

Author :
    Dracudar

Version:
    1.3

Date de création :
    2026.07.05

Date de modification:
    2026.07.13
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
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
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
from src.modules.stats.backend.sumup import (
    comptes_disponibles,
    grouper_transactions,
    horodatage_commande,
    lire_lignes_csv,
    rapprocher_paiements_carte,
    suggerer_commandes_probables,
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

# Largeur maximale de la "feuille" de contenu (page Général / pages par plat),
# centrée dans la zone défilante — évite que les tableaux à peu de colonnes ne
# s'étirent sur toute la largeur de l'écran, et se rapproche du rendu du PDF exporté.
_LARGEUR_FEUILLE = 850

# Largeur fixe du volet de navigation latéral (Général / Plats), toujours visible.
_LARGEUR_NAV = 190


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
        self._sumup_lignes: List[Dict[str, str]] = []
        self._sumup_chemin: Optional[str] = None
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

        corps_layout = QHBoxLayout()
        corps_layout.setSpacing(0)
        corps_layout.addWidget(self._build_nav_tree())

        self.content_stack = QStackedWidget()
        corps_layout.addWidget(self.content_stack, 1)
        main_layout.addLayout(corps_layout, 1)

        page_generale, self.general_layout = self._build_page_generale()
        self.content_stack.addWidget(page_generale)
        self._item_general.setData(0, Qt.ItemDataRole.UserRole, page_generale)
        self.nav_tree.setCurrentItem(self._item_general)

        page_sumup, sumup_layout = self._build_page_generale()
        self._build_sumup_controls(sumup_layout)
        self.content_stack.addWidget(page_sumup)
        self._item_sumup.setData(0, Qt.ItemDataRole.UserRole, page_sumup)

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
            QLabel#titrePlat {{
                color: {_TEXT_TITLE};
                font-size: 20px;
                font-weight: 700;
                text-decoration: underline;
                padding: 4px 0 10px 0;
            }}
            QLineEdit, QComboBox, QSpinBox {{
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
            QTreeWidget#navStats {{
                background-color: {_BG_CARD};
                border: 1px solid {_BORDER_CARD};
                outline: none;
                padding: 4px 0;
            }}
            QTreeWidget#navStats::item {{
                color: {_TEXT_MUTED};
                border: none;
                padding: 8px 10px;
            }}
            QTreeWidget#navStats::item:selected {{
                background-color: {_BG_MAIN};
                color: {_TEXT_TITLE};
            }}
            QTreeWidget#navStats::item:hover:!selected {{
                color: {_TEXT_TITLE};
            }}
            QTreeWidget#navStats::branch {{
                background: transparent;
                border: none;
            }}
            QTreeWidget#navStats::branch:selected {{
                background-color: {_BG_MAIN};
            }}
            """
        )

    def _build_scrollable_page(self, couleur_fond: str) -> tuple:
        """Crée une zone défilante contenant une "feuille" centrée à largeur fixe (~format A4),
        pour que le contenu (tableaux, cartes, graphiques) ne s'étire pas sur toute la largeur
        de l'écran et se rapproche du rendu du PDF exporté.

        :return: tuple (scroll_area, content_layout) — le layout est à remplir.
        """
        scroll_area = ScrollAreaTactile(couleur_fond)

        feuille = QWidget()
        feuille.setMaximumWidth(_LARGEUR_FEUILLE)
        content_layout = QVBoxLayout(feuille)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        centreur = QWidget()
        centreur_layout = QHBoxLayout(centreur)
        centreur_layout.setContentsMargins(0, 0, 0, 0)
        centreur_layout.addStretch()
        centreur_layout.addWidget(feuille)
        centreur_layout.addStretch()

        scroll_area.setWidget(centreur)
        return scroll_area, content_layout

    def _build_nav_tree(self) -> QTreeWidget:
        """Construit le volet de navigation latéral (Général / Plats / Rapprochement SumUp),
        toujours visible.

        "Général" et "Rapprochement SumUp" sont des items de premier niveau sélectionnables ;
        "Plats" est un en-tête de regroupement non sélectionnable dont les enfants (un par
        plat) sont ajoutés/retirés à chaque rafraîchissement dans _render_par_plat. L'arbre
        reste toujours développé (pas de repli/dépli manuel) : la place disponible en largeur
        (feuille au format A4) permet de garder cette navigation visible en permanence plutôt
        que dans des onglets.
        """
        self.nav_tree = QTreeWidget()
        self.nav_tree.setObjectName("navStats")
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setRootIsDecorated(False)
        self.nav_tree.setItemsExpandable(False)
        self.nav_tree.setFixedWidth(_LARGEUR_NAV)

        self._item_general = QTreeWidgetItem(["Général"])
        self.nav_tree.addTopLevelItem(self._item_general)

        self._item_plats = QTreeWidgetItem(["Plats"])
        self._item_plats.setFlags(self._item_plats.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        police_en_tete = self._item_plats.font(0)
        police_en_tete.setBold(True)
        self._item_plats.setFont(0, police_en_tete)
        self.nav_tree.addTopLevelItem(self._item_plats)
        self._item_plats.setExpanded(True)

        self._nav_items_plats: Dict[str, QTreeWidgetItem] = {}

        self._item_sumup = QTreeWidgetItem(["Rapprochement SumUp"])
        self.nav_tree.addTopLevelItem(self._item_sumup)

        self.nav_tree.currentItemChanged.connect(self._on_nav_item_selected)
        return self.nav_tree

    def _on_nav_item_selected(self, current: Optional[QTreeWidgetItem], previous: Optional[QTreeWidgetItem]):
        """Bascule le content_stack sur la page associée à l'item de navigation sélectionné."""
        if current is None or current is self._item_plats:
            if previous is not None:
                self.nav_tree.setCurrentItem(previous)
            return
        page = current.data(0, Qt.ItemDataRole.UserRole)
        if page is not None:
            self.content_stack.setCurrentWidget(page)

    def _build_page_generale(self) -> tuple:
        """Crée la page défilante "Général".

        :return: tuple (page, content_layout) — le layout est à remplir, la page à ajouter au content_stack.
        """
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area, content_layout = self._build_scrollable_page(_BG_MAIN)
        page_layout.addWidget(scroll_area)

        return page, content_layout

    def _build_page_plat_scrollable(self) -> tuple:
        """Crée une page défilante pour un plat, destinée au content_stack.

        :return: tuple (page, content_layout) — le layout est à remplir, la page à ajouter au content_stack.
        """
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area, content_layout = self._build_scrollable_page(_BG_CARD)
        page_layout.addWidget(scroll_area)

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

    # ── Rapprochement SumUp ──────────────────────────────────────────────────

    def _build_sumup_controls(self, layout: QVBoxLayout):
        """Construit la page "Rapprochement SumUp" : sélection du relevé CSV et du
        compte (TPE), lancement du rapprochement et affichage des écarts trouvés."""
        titre = QLabel("Rapprochement des paiements carte (SumUp)")
        titre.setObjectName("titrePlat")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titre)

        note = QLabel(
            "Compare les commandes de l'app payées par carte au relevé de ventes CSV "
            "exporté depuis SumUp, pour repérer les écarts de saisie du moyen de "
            "paiement (montant + date/heure, avec une tolérance car la validation sur "
            "l'app est manuelle)."
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(note)

        ligne_fichier = QHBoxLayout()
        self.sumup_fichier_btn = QPushButton("  Choisir le relevé CSV...")
        self.sumup_fichier_btn.setIcon(icone("card.svg", 18))
        self.sumup_fichier_btn.setIconSize(QSize(18, 18))
        self.sumup_fichier_btn.clicked.connect(self._on_choisir_fichier_sumup)
        ligne_fichier.addWidget(self.sumup_fichier_btn)
        self.sumup_fichier_label = QLabel("Aucun fichier sélectionné")
        self.sumup_fichier_label.setStyleSheet(f"color: {_TEXT_MUTED};")
        ligne_fichier.addWidget(self.sumup_fichier_label, 1)
        layout.addLayout(ligne_fichier)

        ligne_options = QHBoxLayout()
        label_compte = QLabel("Compte (TPE) :")
        label_compte.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px;")
        ligne_options.addWidget(label_compte)
        self.sumup_compte_combo = QComboBox()
        self.sumup_compte_combo.setEnabled(False)
        ligne_options.addWidget(self.sumup_compte_combo, 1)

        label_tolerance = QLabel("Tolérance (min) :")
        label_tolerance.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px;")
        ligne_options.addWidget(label_tolerance)
        self.sumup_tolerance_spin = QSpinBox()
        self.sumup_tolerance_spin.setRange(1, 60)
        self.sumup_tolerance_spin.setValue(5)
        self.sumup_tolerance_spin.setMaximumWidth(70)
        ligne_options.addWidget(self.sumup_tolerance_spin)
        layout.addLayout(ligne_options)

        self.sumup_verifier_btn = QPushButton("  Lancer la vérification")
        self.sumup_verifier_btn.setIcon(icone("check.svg", 18))
        self.sumup_verifier_btn.setIconSize(QSize(18, 18))
        self.sumup_verifier_btn.setEnabled(False)
        self.sumup_verifier_btn.clicked.connect(self._on_verifier_sumup)
        layout.addWidget(self.sumup_verifier_btn)

        self.sumup_resultats_container = QWidget()
        self.sumup_resultats_layout = QVBoxLayout(self.sumup_resultats_container)
        self.sumup_resultats_layout.setContentsMargins(0, 12, 0, 0)
        self.sumup_resultats_layout.setSpacing(10)
        layout.addWidget(self.sumup_resultats_container)

        layout.addStretch()

    def _on_choisir_fichier_sumup(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner le relevé de ventes SumUp", "", "CSV (*.csv)",
        )
        if not chemin:
            return

        try:
            lignes = lire_lignes_csv(chemin)
        except OSError as e:
            QMessageBox.warning(self, "Relevé SumUp", f"Impossible de lire le fichier :\n{e}")
            return

        comptes = comptes_disponibles(lignes)
        if not comptes:
            QMessageBox.warning(
                self, "Relevé SumUp",
                "Aucune colonne \"Compte\" exploitable n'a été trouvée dans ce fichier.",
            )
            return

        self._sumup_lignes = lignes
        self._sumup_chemin = chemin
        self.sumup_fichier_label.setText(Path(chemin).name)

        self.sumup_compte_combo.clear()
        self.sumup_compte_combo.addItems(comptes)
        self.sumup_compte_combo.setEnabled(True)
        self.sumup_verifier_btn.setEnabled(True)
        self._clear_layout(self.sumup_resultats_layout)

    def _commandes_carte(self) -> List[Dict[str, Any]]:
        """Construit la liste des commandes de l'historique payées par carte, dans la
        période filtrée en haut de page : {id, datetime, montant}."""
        date_from = self._parse_date(self.date_from_field.text(), "00:00")
        date_to = self._parse_date(self.date_to_field.text(), "23:59")

        commandes = []
        for order in get_all_history_orders():
            if (order.get("payment_type") or "") != "Carte":
                continue
            dt = horodatage_commande(order.get("validation_at"))
            if date_from and (dt is None or dt < date_from):
                continue
            if date_to and (dt is None or dt > date_to):
                continue
            commandes.append({
                "id": order.get("id", ""),
                "datetime": dt,
                "montant": order.get("amount") or 0,
                "status": order.get("status", ""),
            })
        return commandes

    def _toutes_commandes(self, exclure_ids: set) -> List[Dict[str, Any]]:
        """Construit la liste de TOUTES les commandes de l'historique (quel que soit le
        moyen de paiement), dans la période filtrée en haut de page, à l'exclusion des ID
        donnés — sert de vivier de candidats pour suggerer_commandes_probables, afin de
        repérer une commande dont le moyen de paiement aurait été mal saisi sur l'app."""
        date_from = self._parse_date(self.date_from_field.text(), "00:00")
        date_to = self._parse_date(self.date_to_field.text(), "23:59")

        commandes = []
        for order in get_all_history_orders():
            id_ = order.get("id", "")
            if id_ in exclure_ids:
                continue
            dt = horodatage_commande(order.get("validation_at"))
            if date_from and (dt is None or dt < date_from):
                continue
            if date_to and (dt is None or dt > date_to):
                continue
            commandes.append({
                "id": id_,
                "datetime": dt,
                "montant": order.get("amount") or 0,
                "payment_type": order.get("payment_type") or "Inconnu",
                "status": order.get("status", ""),
            })
        return commandes

    def _on_verifier_sumup(self):
        compte = self.sumup_compte_combo.currentText()
        if not compte:
            return

        transactions = grouper_transactions(self._sumup_lignes, compte)
        commandes_carte = self._commandes_carte()
        tolerance = self.sumup_tolerance_spin.value()

        resultat = rapprocher_paiements_carte(commandes_carte, transactions, tolerance_minutes=tolerance)

        ids_apparies = {p["commande"]["id"] for p in resultat["paires"]}
        commandes_candidates = self._toutes_commandes(ids_apparies)
        suggestions = suggerer_commandes_probables(
            resultat["transactions_sans_correspondance"], commandes_candidates, tolerance_minutes=tolerance,
        )

        self._afficher_resultats_sumup(resultat, suggestions, len(commandes_carte), len(transactions))

        logger.log(logger.RAPPROCHEMENT_SUMUP, {
            "fichier": self._sumup_chemin,
            "compte": compte,
            "tolerance_minutes": tolerance,
            "nb_commandes_carte": len(commandes_carte),
            "nb_transactions_sumup": len(transactions),
            "nb_paires": len(resultat["paires"]),
            "nb_ecarts": len(resultat["commandes_sans_correspondance"]) + len(resultat["transactions_sans_correspondance"]),
        })

    def _afficher_resultats_sumup(
        self, resultat: Dict[str, Any], suggestions: Dict[str, List[Dict[str, Any]]],
        nb_commandes: int, nb_transactions: int,
    ):
        self._clear_layout(self.sumup_resultats_layout)

        resume = QLabel(
            f"{len(resultat['paires'])} paiement(s) rapproché(s) sur {nb_commandes} commande(s) carte "
            f"et {nb_transactions} transaction(s) SumUp."
        )
        resume.setWordWrap(True)
        resume.setStyleSheet(f"color: {_TEXT_TITLE}; font-size: 13px; font-weight: 600;")
        self.sumup_resultats_layout.addWidget(resume)

        commandes_orphelines = resultat["commandes_sans_correspondance"]
        self.sumup_resultats_layout.addWidget(self._build_section_title(
            f"Paiements carte sur l'app sans transaction SumUp ({len(commandes_orphelines)})"
        ))
        if commandes_orphelines:
            lignes = [
                [c["id"], self._formater_datetime(c["datetime"]), f"{c['montant']:.2f} €", c.get("status", "")]
                for c in commandes_orphelines
            ]
            self.sumup_resultats_layout.addWidget(
                self._build_table(["Commande", "Date/heure", "Montant", "Statut"], lignes)
            )
        else:
            self.sumup_resultats_layout.addWidget(self._label_vide("Aucun écart."))

        transactions_orphelines = resultat["transactions_sans_correspondance"]
        self.sumup_resultats_layout.addWidget(self._build_section_title(
            f"Transactions SumUp sans commande carte correspondante ({len(transactions_orphelines)})"
        ))
        if transactions_orphelines:
            note_suggestions = QLabel(
                "\"Commande probable\" : commande de l'app (tout moyen de paiement confondu) au "
                "même montant et à une date/heure proche — vérifiez si son moyen de paiement a été "
                "mal saisi."
            )
            note_suggestions.setWordWrap(True)
            note_suggestions.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
            self.sumup_resultats_layout.addWidget(note_suggestions)

            lignes = [
                [
                    t["reference"],
                    self._formater_datetime(t["datetime"]) if t["lisible"] else "(date illisible)",
                    f"{t['montant']:.2f} €",
                    t.get("moyen_paiement", ""),
                    self._formater_suggestion(suggestions.get(t["reference"], [])),
                ]
                for t in transactions_orphelines
            ]
            self.sumup_resultats_layout.addWidget(
                self._build_table(
                    ["Référence", "Date/heure", "Montant", "Moyen de paiement", "Commande probable"], lignes,
                )
            )
        else:
            self.sumup_resultats_layout.addWidget(self._label_vide("Aucun écart."))

    def _formater_suggestion(self, candidats: List[Dict[str, Any]]) -> str:
        """Formate la (les) commande(s) candidate(s) suggérée(s) pour une transaction SumUp
        sans correspondance : la plus proche en date/heure, plus un décompte des autres."""
        if not candidats:
            return "—"
        meilleur = candidats[0]
        texte = f"{meilleur['id']} ({meilleur['payment_type']}, écart {meilleur['ecart_minutes']:.1f} min)"
        if len(candidats) > 1:
            texte += f" (+{len(candidats) - 1} autre(s))"
        return texte

    def _label_vide(self, texte: str) -> QLabel:
        label = QLabel(texte)
        label.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px; padding: 4px 0;")
        return label

    def _formater_datetime(self, dt: Optional[datetime]) -> str:
        return dt.strftime("%d/%m/%Y %H:%M") if dt else "(date illisible)"

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
        """Reconstruit les entrées "Plats" du volet de navigation et leurs pages associées : une
        entrée par plat présent dans la période, avec un contenu plus ou moins riche selon les
        données disponibles pour ce type de plat (recettes pour la pizza, composition pour les
        plats personnalisables, temps de préparation/retrait si mesurés, ou simplement les
        totaux de vente pour un plat simple).
        """
        item_courant = self.nav_tree.currentItem()
        etait_sur_general = item_courant is self._item_general
        nom_plat_precedent = (
            item_courant.text(0)
            if item_courant is not None and item_courant.parent() is self._item_plats
            else None
        )

        self.nav_tree.blockSignals(True)
        for item in list(self._nav_items_plats.values()):
            widget = item.data(0, Qt.ItemDataRole.UserRole)
            self._item_plats.removeChild(item)
            if widget is not None:
                self.content_stack.removeWidget(widget)
                widget.deleteLater()
        self._nav_items_plats.clear()

        plats = self._stats.get("plats", [])
        temps_prepa_par_plat = {p["plat"]: p for p in self._temps_preparation.get("par_plat", [])}
        delais_par_plat = {p["plat"]: p for p in self._delais_livraison.get("par_plat", [])}
        temps_prepa_heures = self._temps_preparation.get("par_plat_et_heure", {})
        delais_heures = self._delais_livraison.get("par_plat_et_heure", {})

        for info_plat in sorted(plats, key=lambda p: p["nom"]):
            nom = info_plat["nom"]
            page, layout = self._build_page_plat_scrollable()
            self._render_page_plat(
                layout, info_plat,
                temps_prepa_par_plat.get(nom), delais_par_plat.get(nom), self._composition.get(nom),
                temps_prepa_heures.get(nom, []), delais_heures.get(nom, []),
            )
            self.content_stack.addWidget(page)
            item = QTreeWidgetItem([nom])
            item.setData(0, Qt.ItemDataRole.UserRole, page)
            self._item_plats.addChild(item)
            self._nav_items_plats[nom] = item

        if not plats:
            page, layout = self._build_page_plat_scrollable()
            vide = QLabel("Aucun plat vendu sur cette période.")
            vide.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vide.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 14px; padding: 20px;")
            layout.addWidget(vide)
            layout.addStretch()
            self.content_stack.addWidget(page)
            item = QTreeWidgetItem(["—"])
            item.setData(0, Qt.ItemDataRole.UserRole, page)
            self._item_plats.addChild(item)
            self._nav_items_plats["—"] = item

        self.nav_tree.blockSignals(False)

        if etait_sur_general:
            cible = self._item_general
        else:
            cible = self._nav_items_plats.get(nom_plat_precedent) or next(
                iter(self._nav_items_plats.values()), self._item_general,
            )
        self.nav_tree.setCurrentItem(cible)

    def _render_page_plat(
        self, layout: QVBoxLayout, info_plat: Dict[str, Any],
        temps_prepa: Optional[Dict[str, Any]], delais: Optional[Dict[str, Any]],
        composition: Optional[Dict[str, Any]],
        temps_prepa_heures: List[Dict[str, Any]], delais_heures: List[Dict[str, Any]],
    ):
        nom = info_plat["nom"]

        titre = QLabel(nom)
        titre.setObjectName("titrePlat")
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titre)

        layout.addWidget(self._build_cartes_row([
            ("Quantité vendue", str(info_plat["quantite"])),
            ("Prix moyen", f"{info_plat['prix_moyen']:.2f} €"),
            ("Montant", f"{info_plat['montant']:.2f} €"),
        ]))

        self._ajouter_section_delai(layout, "Délais de préparation", temps_prepa, temps_prepa_heures)
        self._ajouter_section_delai(layout, "Délais de livraison", delais, delais_heures)

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

    def _ajouter_section_delai(
        self, layout: QVBoxLayout, titre: str,
        stats_delai: Optional[Dict[str, Any]], par_heure: List[Dict[str, Any]],
    ):
        """Ajoute au layout une section délai (Moyenne/Minimum/Maximum + graphique horaire), si mesurée."""
        if not stats_delai:
            return
        layout.addWidget(self._build_section_title(titre))
        layout.addWidget(self._build_table_delai_compact(stats_delai))
        if len(par_heure) > 1:
            layout.addWidget(self._build_bar_chart(
                [h["heure"] for h in par_heure], [h["temps_moyen_minutes"] for h in par_heure], "Minutes",
            ))

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

    def _build_table_delai_compact(self, stats_delai: Dict[str, Any]) -> QTableWidget:
        """Tableau compact (une ligne) Moyenne/Minimum/Maximum pour un délai d'un plat donné."""
        lignes = [[
            f"{stats_delai['temps_moyen_minutes']:.1f} min",
            f"{stats_delai['temps_min_minutes']:.1f} min",
            f"{stats_delai['temps_max_minutes']:.1f} min",
        ]]
        return self._build_table(["Moyenne", "Minimum", "Maximum"], lignes)

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
