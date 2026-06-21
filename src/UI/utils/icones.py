#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
icones.py

Description:
    Utilitaires de rendu d'icônes SVG pour les widgets Qt : recadrage automatique
    sur le tracé réel (les fichiers sources contiennent souvent une marge ou un
    décalage variable dans leur viewBox, source d'incohérences de taille et de
    centrage une fois mis à l'échelle) et recoloration en aplat pour la
    lisibilité sur fond sombre ou clair.

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.06.21

Date de modification:
    2026.06.21
"""

from PySide6.QtCore import QRect, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from src.backend.app_config import get_assets_path

_RESOLUTION_BASE = 128  # passe légère : suffisante pour détecter le tracé réel
_RESOLUTION_MAX = 1024  # plafond de sécurité pour la passe haute résolution
_MARGE_QUALITE = 1.5  # marge au-delà de la taille cible, pour un dernier lissage net


def _vers_qsize(taille: int | QSize) -> QSize:
    """Normalise une taille en QSize : un int produit un carré (taille, taille)."""
    return taille if isinstance(taille, QSize) else QSize(taille, taille)


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


def _rendu_svg(chemin_svg: str, resolution: int) -> QImage:
    """Rend un SVG dans un canvas carré transparent de la résolution donnée."""
    renderer = QSvgRenderer(chemin_svg)
    image = QImage(resolution, resolution, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, resolution, resolution))
    painter.end()
    return image


def _rendu_recadre(chemin_svg: str, taille: QSize, recadrer: bool) -> tuple[QImage, QRect]:
    """Rend un SVG net à la résolution nécessaire pour la taille demandée, et
    retourne l'image avec le rectangle à utiliser comme source (tracé réel si
    recadrer, image entière sinon).

    Le tracé réel est d'abord détecté sur un rendu basse résolution (rapide à
    scanner pixel par pixel), puis remis à l'échelle géométriquement si la
    taille cible l'exige — un second rendu vectoriel direct à la résolution
    nécessaire, jamais un agrandissement du premier rendu (qui produirait du
    flou et perdrait l'intérêt du format vectoriel).
    """
    rendu = _rendu_svg(chemin_svg, _RESOLUTION_BASE)
    trace = _rect_trace_opaque(rendu) if recadrer else rendu.rect()

    echelle_necessaire = max(taille.width() / trace.width(), taille.height() / trace.height())
    if echelle_necessaire > 1:
        resolution = min(round(_RESOLUTION_BASE * echelle_necessaire * _MARGE_QUALITE), _RESOLUTION_MAX)
        ratio = resolution / _RESOLUTION_BASE
        rendu = _rendu_svg(chemin_svg, resolution)
        trace = QRect(
            round(trace.x() * ratio),
            round(trace.y() * ratio),
            round(trace.width() * ratio),
            round(trace.height() * ratio),
        )

    return rendu, trace


def pixmap_depuis_svg(chemin_svg: str, taille: int | QSize, *, recadrer: bool = True) -> QPixmap:
    """Charge un fichier SVG (chemin absolu ou relatif) et le rastérise, mis à
    l'échelle et centré dans la taille demandée, sans recoloration."""
    taille = _vers_qsize(taille)
    rendu, trace = _rendu_recadre(chemin_svg, taille, recadrer)

    pixmap = QPixmap(taille)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    echelle = min(taille.width() / trace.width(), taille.height() / trace.height())
    largeur_cible = round(trace.width() * echelle)
    hauteur_cible = round(trace.height() * echelle)
    cible = QRect(
        (taille.width() - largeur_cible) // 2,
        (taille.height() - hauteur_cible) // 2,
        largeur_cible,
        hauteur_cible,
    )
    painter.drawImage(cible, rendu, trace)
    painter.end()
    return pixmap


def icone(nom_fichier: str, taille: int | QSize, *, recadrer: bool = True) -> QIcon:
    """Charge une icône SVG depuis assets/icons/ (sans recoloration)."""
    return QIcon(pixmap_depuis_svg(get_assets_path("icons", nom_fichier), taille, recadrer=recadrer))


def _pixmap_coloree(
    nom_fichier: str, couleur: str, taille: int | QSize, *, recadrer: bool = True
) -> QPixmap:
    pixmap = pixmap_depuis_svg(get_assets_path("icons", nom_fichier), taille, recadrer=recadrer)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(couleur))
    painter.end()
    return pixmap


def icone_coloree(
    nom_fichier: str, couleur: str, taille: int | QSize, *, recadrer: bool = True
) -> QIcon:
    """Charge une icône SVG depuis assets/icons/, recadrée sur son tracé réel et
    recolorée en aplat (les SVG sources conservant leurs couleurs d'origine
    sinon)."""
    return QIcon(_pixmap_coloree(nom_fichier, couleur, taille, recadrer=recadrer))


def icone_action(
    nom_fichier: str,
    taille: int | QSize,
    couleur_normale: str,
    couleur_desactivee: str,
    *,
    recadrer: bool = True,
) -> QIcon:
    """Charge une icône SVG avec deux états colorés (normal / désactivé), pour
    les boutons d'action dont l'icône doit s'effacer visuellement quand le
    bouton est désactivé (ex. annulation)."""
    icon = QIcon()
    icon.addPixmap(
        _pixmap_coloree(nom_fichier, couleur_normale, taille, recadrer=recadrer),
        QIcon.Mode.Normal,
    )
    icon.addPixmap(
        _pixmap_coloree(nom_fichier, couleur_desactivee, taille, recadrer=recadrer),
        QIcon.Mode.Disabled,
    )
    return icon
