#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_export.py - Export du rapport de statistiques en PDF

Description:
    Génère un compte rendu PDF à partir du dict produit par
    stats.calculer_statistiques : totaux, graphiques (répartition par plat,
    par moyen de paiement) et tableaux détaillés (plats, paiements, recettes
    pizza le cas échéant).

Author :
    Dracudar

Version:
    1.2

Date de création :
    2026.07.05

Date de modification:
    2026.07.16
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Sequence

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.modules.stats.backend.stats import (
    SEUIL_JOURS_AFFLUENCE_DETAILLEE,
    SEUIL_JOURS_AFFLUENCE_HEBDOMADAIRE,
)

_PALETTE = [
    colors.HexColor("#4a7fcb"),
    colors.HexColor("#d4a017"),
    colors.HexColor("#4caf50"),
    colors.HexColor("#c0392b"),
    colors.HexColor("#9b59b6"),
    colors.HexColor("#c97a30"),
    colors.HexColor("#5865f2"),
]

_STYLE_ENTETE_TABLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3a3d43")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c0c0c0")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
])


def _feuille_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitrePrincipal", fontSize=20, leading=24, spaceAfter=4, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SousTitre", fontSize=12, leading=16, textColor=colors.HexColor("#555555"), spaceAfter=16))
    styles.add(ParagraphStyle(name="TitreSection", fontSize=14, leading=18, spaceBefore=14, spaceAfter=8, fontName="Helvetica-Bold"))
    return styles


def _graphique_barres(libelles: Sequence[str], valeurs: Sequence[float], largeur=17 * cm, hauteur=7 * cm) -> Drawing:
    """Construit un histogramme vertical (une série) à partir de libellés/valeurs."""
    dessin = Drawing(largeur, hauteur)
    graphique = VerticalBarChart()
    graphique.x = 50
    graphique.y = 40
    graphique.width = largeur - 80
    graphique.height = hauteur - 60
    graphique.data = [list(valeurs)]
    graphique.categoryAxis.categoryNames = list(libelles)
    graphique.categoryAxis.labels.angle = 45
    graphique.categoryAxis.labels.dy = -12
    graphique.categoryAxis.labels.fontSize = 8
    graphique.valueAxis.valueMin = 0
    graphique.bars[0].fillColor = _PALETTE[0]
    dessin.add(graphique)
    return dessin


def _graphique_camembert(libelles: Sequence[str], valeurs: Sequence[float], largeur=17 * cm, hauteur=7 * cm) -> Drawing:
    """Construit un camembert avec légende texte à droite (labels courts sous chaque part)."""
    dessin = Drawing(largeur, hauteur)
    camembert = Pie()
    camembert.x = 20
    camembert.y = hauteur / 2 - 60
    camembert.width = 120
    camembert.height = 120
    camembert.data = list(valeurs)
    camembert.labels = [f"{lib} ({val:.0f})" for lib, val in zip(libelles, valeurs)]
    camembert.simpleLabels = 1
    camembert.slices.strokeWidth = 0.5
    for i in range(len(valeurs)):
        camembert.slices[i].fillColor = _PALETTE[i % len(_PALETTE)]
    dessin.add(camembert)
    return dessin


def _tableau_totaux(totaux: Dict[str, Any]) -> Table:
    data = [
        ["Commandes", "Montant total", "Panier moyen", "Plats vendus"],
        [
            str(totaux.get("nb_commandes", 0)),
            f"{totaux.get('montant_total', 0):.2f} €",
            f"{totaux.get('panier_moyen', 0):.2f} €",
            str(totaux.get("nb_plats", 0)),
        ],
    ]
    table = Table(data, colWidths=[4.25 * cm] * 4)
    table.setStyle(_STYLE_ENTETE_TABLE)
    return table


def _tableau_plats(plats: List[Dict[str, Any]]) -> Table:
    data = [["Plat", "Quantité", "Prix moyen", "Montant"]]
    for p in plats:
        data.append([
            p["nom"], str(p["quantite"]), f"{p['prix_moyen']:.2f} €", f"{p['montant']:.2f} €",
        ])
    table = Table(data, colWidths=[6 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
    table.setStyle(_STYLE_ENTETE_TABLE)
    return table


def _tableau_paiements(paiements: List[Dict[str, Any]]) -> Table:
    data = [["Moyen de paiement", "Quantité", "% commandes", "Montant"]]
    for p in paiements:
        data.append([
            p["type"], str(p["quantite"]), f"{p['pourcentage']:.1f} %", f"{p['montant']:.2f} €",
        ])
    table = Table(data, colWidths=[6 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
    table.setStyle(_STYLE_ENTETE_TABLE)
    return table


def _tableau_recettes(recettes: List[Dict[str, Any]]) -> Table:
    data = [["Recette pizza", "Quantité", "% pizzas"]]
    for r in recettes:
        data.append([r["recette"], str(r["quantite"]), f"{r['pourcentage']:.1f} %"])
    table = Table(data, colWidths=[8 * cm, 4.25 * cm, 4.25 * cm])
    table.setStyle(_STYLE_ENTETE_TABLE)
    return table


def _tableau_durees(par_plat: List[Dict[str, Any]]) -> Table:
    data = [["Plat", "Nb plats", "Moyenne", "Minimum", "Maximum"]]
    for p in par_plat:
        data.append([
            p["plat"], str(p["nb_plats"]),
            f"{p['temps_moyen_minutes']:.1f} min", f"{p['temps_min_minutes']:.1f} min", f"{p['temps_max_minutes']:.1f} min",
        ])
    table = Table(data, colWidths=[5 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm])
    table.setStyle(_STYLE_ENTETE_TABLE)
    return table


def generer_rapport_pdf(
    stats: Dict[str, Any],
    chemin_fichier: str,
    titre_periode: str = "",
    affluence: Dict[str, Any] | None = None,
    temps_preparation: Dict[str, Any] | None = None,
    delais_livraison: Dict[str, Any] | None = None,
) -> None:
    """Génère le rapport PDF de statistiques à l'emplacement demandé.

    :param stats: dict retourné par stats.calculer_statistiques
    :param chemin_fichier: chemin de destination du PDF
    :param titre_periode: texte affiché sous le titre (ex. "Du 01/07/2026 au 05/07/2026")
    :param affluence: dict retourné par stats.calculer_affluence (optionnel)
    :param temps_preparation: dict retourné par stats.calculer_temps_preparation (optionnel)
    :param delais_livraison: dict retourné par stats.calculer_delais_livraison (optionnel)
    """
    styles = _feuille_styles()
    document = SimpleDocTemplate(
        chemin_fichier, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    elements: List[Any] = []

    elements.append(Paragraph("Rapport de statistiques — Morphoz Snack", styles["TitrePrincipal"]))
    sous_titre = titre_periode or "Toutes périodes confondues"
    sous_titre += f"  ·  généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    elements.append(Paragraph(sous_titre, styles["SousTitre"]))

    elements.append(Paragraph("Totaux", styles["TitreSection"]))
    elements.append(_tableau_totaux(stats["totaux"]))

    plats = stats.get("plats", [])
    if plats:
        elements.append(Paragraph("Ventilation par plat", styles["TitreSection"]))
        top_plats = plats[:8]
        elements.append(_graphique_barres(
            [p["nom"] for p in top_plats], [p["quantite"] for p in top_plats],
        ))
        elements.append(Spacer(1, 8))
        elements.append(_tableau_plats(plats))

    paiements = stats.get("paiements", [])
    if paiements:
        elements.append(Paragraph("Répartition des moyens de paiement", styles["TitreSection"]))
        elements.append(_graphique_camembert(
            [p["type"] for p in paiements], [p["quantite"] for p in paiements],
        ))
        elements.append(Spacer(1, 8))
        elements.append(_tableau_paiements(paiements))

    recettes = stats.get("recettes_pizza", [])
    if recettes:
        elements.append(Paragraph("Recettes pizza les plus vendues", styles["TitreSection"]))
        elements.append(_tableau_recettes(recettes))

    ca_par_jour = stats.get("ca_par_jour", [])
    if len(ca_par_jour) > 1:
        elements.append(Paragraph("Chiffre d'affaires par jour", styles["TitreSection"]))
        elements.append(_graphique_barres(
            [j["date"] for j in ca_par_jour], [j["montant"] for j in ca_par_jour],
        ))

    affluence = affluence or {}
    par_jour_affluence = affluence.get("par_jour", [])
    totaux_affluence = affluence.get("totaux", {})
    if totaux_affluence.get("nb_commandes_validees"):
        elements.append(Paragraph("Horaires d'affluence", styles["TitreSection"]))
        elements.append(Paragraph(
            f"{totaux_affluence.get('nb_commandes_validees', 0)} commande(s) validée(s) prise(s) en compte, "
            f"dont {totaux_affluence.get('nb_annulees', 0)} annulée(s) (basé sur l'heure de validation, "
            "indépendamment du statut final).",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 6))

        nb_jours_affluence = len(par_jour_affluence)
        if nb_jours_affluence <= SEUIL_JOURS_AFFLUENCE_DETAILLEE:
            # Période courte (événement de quelques jours, suivi jusqu'à la semaine) : un
            # graphique horaire par jour pour ne pas cumuler des dates différentes dans les
            # mêmes tranches horaires.
            for jour in par_jour_affluence:
                elements.append(Paragraph(jour["date"], styles["Normal"]))
                elements.append(_graphique_barres(
                    [h["heure"] for h in jour["par_heure"]], [h["quantite"] for h in jour["par_heure"]],
                ))
                elements.append(Spacer(1, 6))
        else:
            # Période longue : le détail horaire n'est plus lisible ni pertinent. On affiche la
            # moyenne quotidienne, puis une agrégation par semaine (jusqu'à environ un mois) ou
            # par mois (au-delà) plutôt qu'un graphique par jour.
            elements.append(Paragraph(
                f"Moyenne journalière : {affluence.get('moyenne_par_jour', 0):.1f} commande(s).",
                styles["Normal"],
            ))
            elements.append(Spacer(1, 6))
            if nb_jours_affluence <= SEUIL_JOURS_AFFLUENCE_HEBDOMADAIRE:
                elements.append(Paragraph("Commandes validées par semaine (date du lundi)", styles["Normal"]))
                par_semaine = affluence.get("par_semaine", [])
                elements.append(_graphique_barres(
                    [s["semaine"] for s in par_semaine], [s["quantite"] for s in par_semaine],
                ))
            else:
                elements.append(Paragraph("Commandes validées par mois", styles["Normal"]))
                par_mois = affluence.get("par_mois", [])
                elements.append(_graphique_barres(
                    [m["mois"] for m in par_mois], [m["quantite"] for m in par_mois],
                ))

    temps_preparation = temps_preparation or {}
    par_plat_prepa = temps_preparation.get("par_plat", [])
    if par_plat_prepa:
        elements.append(Paragraph("Temps de préparation par type de plat", styles["TitreSection"]))
        elements.append(_graphique_barres(
            [p["plat"] for p in par_plat_prepa], [p["temps_moyen_minutes"] for p in par_plat_prepa],
        ))
        elements.append(Spacer(1, 8))
        elements.append(_tableau_durees(par_plat_prepa))

    delais_livraison = delais_livraison or {}
    par_plat_delais = delais_livraison.get("par_plat", [])
    if par_plat_delais:
        elements.append(Paragraph("Délai de retrait (plat prêt -&gt; remis au client)", styles["TitreSection"]))
        elements.append(_graphique_barres(
            [p["plat"] for p in par_plat_delais], [p["temps_moyen_minutes"] for p in par_plat_delais],
        ))
        elements.append(Spacer(1, 8))
        elements.append(_tableau_durees(par_plat_delais))

    document.build(elements)
