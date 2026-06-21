#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
volet_navigation.py

Description:
    Volet de navigation latéral tactile avec raccourcis et icônes.
    S'affiche en superposition sur le contenu principal.

Author :
    Dracudar

Version:
    1.4

Date de création :
    2026.06.13

Date de modification:
    2026.06.21
"""

from PySide6.QtCore import QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QImage, QPainter, QColor, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.backend.app_config import get_assets_path

# ── Palette ───────────────────────────────────────────────────────────────────
_BG          = "#1e2124"
_BG_HOVER    = "#2c2f33"
_BG_ACTIF    = "#4a7fcb"
_CLR_TEXTE   = "#e8e8e8"
_CLR_DANGER  = "#e05c5c"
_CLR_SEP     = "#36393f"
_HAUTEUR_ITEM = 50

_STYLE_ITEM = f"""
    QPushButton {{
        background-color: {_BG};
        color: {_CLR_TEXTE};
        border: none;
        text-align: left;
        padding: 0 20px;
        font-size: 14px;
        min-height: {_HAUTEUR_ITEM}px;
    }}
    QPushButton:hover {{ background-color: {_BG_HOVER}; }}
    QPushButton:checked {{ background-color: {_BG_ACTIF}; font-weight: 700; }}
"""

_STYLE_DANGER = f"""
    QPushButton {{
        background-color: {_BG};
        color: {_CLR_DANGER};
        border: none;
        text-align: left;
        padding: 0 20px;
        font-size: 14px;
        min-height: {_HAUTEUR_ITEM}px;
    }}
    QPushButton:hover {{ background-color: #3a1e1e; }}
"""

_STYLE_FERMER = f"""
    QPushButton {{
        color: #999;
        background: transparent;
        border: none;
        font-size: 18px;
    }}
    QPushButton:hover {{ color: {_CLR_TEXTE}; background-color: {_BG_HOVER}; }}
"""

# (icône SVG, label affiché, identifiant d'action)
# None = séparateur visuel
_ITEMS_NAV = [
    ("saisie.svg",      "Saisie commande",       "saisie"),
    ("prepa.svg",       "Poste de préparation",  "poste_preparation"),
    None,
    ("menu.svg",        "Carte",                 "carte"),
    ("stock.svg",       "Stock",                 "stock"),
    ("historique.svg",  "Historique",            "historique"),
    None,
    ("suivi.svg",       "Affichage extérieur",   "suivi_ext"),
    None,
    ("settings.svg",    "Paramètres",            "parametres"),
    ("log.svg",         "Journal",               "logs"),
]

_ICON_SIZE = QSize(20, 20)
_RESOLUTION_RENDU = 128  # canvas haute résolution utilisé pour détecter le tracé réel


def _rect_trace_opaque(image: QImage) -> QRect:
    """Calcule le rectangle englobant des pixels non transparents d'une image.

    Nécessaire car les SVG sources contiennent une marge variable autour du
    tracé (parfois mal centré dans leur propre viewBox) : sans ce recadrage,
    les icônes apparaissent petites et décentrées une fois mises à l'échelle.
    """
    alpha = image.convertToFormat(QImage.Format.Format_Alpha8)
    largeur, hauteur = alpha.width(), alpha.height()
    octets_par_ligne = alpha.bytesPerLine()
    donnees = bytes(alpha.constBits())[: octets_par_ligne * hauteur]

    haut = bas = gauche = droite = None
    for y in range(hauteur):
        ligne = donnees[y * octets_par_ligne: y * octets_par_ligne + largeur]
        if not any(ligne):
            continue
        if haut is None:
            haut = y
        bas = y
        for x, valeur in enumerate(ligne):
            if valeur:
                if gauche is None or x < gauche:
                    gauche = x
                if droite is None or x > droite:
                    droite = x

    if haut is None:
        return image.rect()
    return QRect(gauche, haut, droite - gauche + 1, bas - haut + 1)


def _icone_coloree(nom_fichier: str, couleur: str) -> QIcon:
    """Charge une icône SVG, recadrée sur son tracé réel et recolorée en aplat
    (lisibilité sur fond sombre, les SVG sources conservant leurs couleurs
    d'origine sinon)."""
    renderer = QSvgRenderer(get_assets_path("icons", nom_fichier))
    rendu = QImage(_RESOLUTION_RENDU, _RESOLUTION_RENDU, QImage.Format.Format_ARGB32_Premultiplied)
    rendu.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rendu)
    renderer.render(painter, QRectF(0, 0, _RESOLUTION_RENDU, _RESOLUTION_RENDU))
    painter.end()

    trace = _rect_trace_opaque(rendu)

    pixmap = QPixmap(_ICON_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    echelle = min(_ICON_SIZE.width() / trace.width(), _ICON_SIZE.height() / trace.height())
    largeur_cible = round(trace.width() * echelle)
    hauteur_cible = round(trace.height() * echelle)
    cible = QRect(
        (_ICON_SIZE.width() - largeur_cible) // 2,
        (_ICON_SIZE.height() - hauteur_cible) // 2,
        largeur_cible,
        hauteur_cible,
    )
    painter.drawImage(cible, rendu, trace)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(couleur))
    painter.end()
    return QIcon(pixmap)


class VoletNavigation(QFrame):
    """Volet de navigation latéral tactile (240 px, superposition sur le contenu)."""

    page_demandee    = Signal(str)  # identifiant de page à afficher
    action_app_demande = Signal(str)  # "fullscreen" | "quit" | "suivi_ext_toggle"
    fermeture_demandee = Signal()  # croix ou item de nav cliqué → la fenêtre parente doit aussi masquer l'overlay

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self._btn_suivi_ext: QPushButton | None = None
        self._btn_plein_ecran: QPushButton | None = None
        self._build_ui()
        self.hide()

    # ── API publique ──────────────────────────────────────────────────────────

    def maj_etat_plein_ecran(self, actif: bool):
        """Met à jour le libellé et l'état coché du bouton plein écran."""
        if self._btn_plein_ecran:
            self._btn_plein_ecran.setChecked(actif)
            self._btn_plein_ecran.setText(
                "  Quitter plein écran" if actif else "  Plein écran"
            )

    def maj_etat_suivi_ext(self, actif: bool):
        """Met à jour l'état coché du bouton affichage extérieur."""
        if self._btn_suivi_ext:
            self._btn_suivi_ext.setChecked(actif)

    # ── Construction ──────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"QFrame {{ background-color: {_BG}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())

        for item in _ITEMS_NAV:
            if item is None:
                layout.addWidget(self._separateur())
            else:
                icone, label, action_id = item
                btn = self._bouton_item(f"  {label}", icone=icone)
                if action_id == "suivi_ext":
                    btn.setCheckable(True)
                    btn.clicked.connect(
                        lambda: self.action_app_demande.emit("suivi_ext_toggle")
                    )
                    self._btn_suivi_ext = btn
                else:
                    btn.clicked.connect(lambda _, p=action_id: self._naviguer(p))
                layout.addWidget(btn)

        layout.addStretch(1)
        layout.addWidget(self._separateur())

        self._btn_plein_ecran = self._bouton_item(
            "  Plein écran", checkable=True, icone="screen.svg"
        )
        self._btn_plein_ecran.clicked.connect(
            lambda: self.action_app_demande.emit("fullscreen")
        )
        layout.addWidget(self._btn_plein_ecran)

        btn_quitter = self._bouton_item(
            "  Quitter", style=_STYLE_DANGER, icone="exit.svg", couleur_icone=_CLR_DANGER
        )
        btn_quitter.clicked.connect(lambda: self.action_app_demande.emit("quit"))
        layout.addWidget(btn_quitter)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet(
            f"background-color: {_BG}; border-bottom: 1px solid {_CLR_SEP};"
        )
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 4, 0)
        layout.setSpacing(0)

        titre = QLabel("Navigation")
        titre.setStyleSheet(
            f"color: {_CLR_TEXTE}; font-size: 13px; font-weight: 700; border: none;"
        )
        layout.addWidget(titre, 1)

        btn_fermer = QPushButton("✕")
        btn_fermer.setFixedSize(44, 44)
        btn_fermer.setStyleSheet(_STYLE_FERMER)
        btn_fermer.clicked.connect(self.fermeture_demandee.emit)
        layout.addWidget(btn_fermer)

        return header

    def _bouton_item(
        self,
        label: str,
        checkable: bool = False,
        style: str = _STYLE_ITEM,
        icone: str | None = None,
        couleur_icone: str = _CLR_TEXTE,
    ) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(checkable)
        btn.setStyleSheet(style)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setFixedHeight(_HAUTEUR_ITEM)
        if icone:
            btn.setIcon(_icone_coloree(icone, couleur_icone))
            btn.setIconSize(_ICON_SIZE)
        return btn

    def _separateur(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {_CLR_SEP}; border: none;")
        return sep

    def _naviguer(self, page_id: str):
        self.page_demandee.emit(page_id)
        self.fermeture_demandee.emit()


class OverlayFermeture(QWidget):
    """
    Fond semi-transparent affiché derrière le volet.
    Un clic sur cet overlay ferme le volet.
    """

    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
