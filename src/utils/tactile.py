#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tactile.py

Description:
    Composants Qt adaptés aux interfaces tactiles.

Author :
    Dracudar
Modified : 2026-06-13
Version : 1.1.0
"""

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QApplication, QFrame, QScrollArea, QScroller, QScrollerProperties, QWidget

# Distance manhattan minimale (en pixels) pour distinguer un tap d'un scroll.
# Un tap naturel peut dériver de 10-15px ; un scroll intentionnel dépasse typiquement 30px.
_SEUIL_SCROLL_PX = 25

# Types d'événements souris à surveiller (vérification rapide avant isAncestorOf)
_TYPES_SOURIS = frozenset({
    QEvent.Type.MouseButtonPress,
    QEvent.Type.MouseMove,
    QEvent.Type.MouseButtonRelease,
})


class _FiltreAntiClickScroll(QObject):
    """
    Filtre global qui consomme le MouseButtonRelease sur les widgets enfants
    d'un ScrollAreaTactile quand le doigt a scrollé, évitant ainsi le
    déclenchement involontaire des boutons cochables pendant le défilement.
    """

    def __init__(self, scroll_area: "ScrollAreaTactile"):
        super().__init__(scroll_area)
        self._scroll_area = scroll_area
        self._pos_pression = None
        self._a_scrolle = False
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        t = event.type()

        # Sortie rapide pour les événements non-souris (la majorité des appels)
        if t not in _TYPES_SOURIS:
            return False

        if not self._est_enfant(obj):
            return False

        if t == QEvent.Type.MouseButtonPress:
            self._pos_pression = event.globalPosition()
            self._a_scrolle = False

        elif t == QEvent.Type.MouseMove and self._pos_pression is not None:
            delta = event.globalPosition() - self._pos_pression
            dist = abs(delta.x()) + abs(delta.y())
            if dist > _SEUIL_SCROLL_PX:
                self._a_scrolle = True

        elif t == QEvent.Type.MouseButtonRelease:
            avait_scrolle = self._a_scrolle
            self._pos_pression = None
            self._a_scrolle = False
            if avait_scrolle:
                return True  # Consommer — empêche le clic involontaire

        return False

    def _est_enfant(self, obj) -> bool:
        if not isinstance(obj, QWidget):
            return False
        try:
            return obj is self._scroll_area or self._scroll_area.isAncestorOf(obj)
        except RuntimeError:
            # Widget peut avoir été détruit entre-temps
            return False


class ScrollAreaTactile(QScrollArea):
    """QScrollArea avec défilement cinétique tactile et scrollbars masquées."""

    def __init__(self, couleur_fond: str = "#2f3136", parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            f"QScrollArea, QScrollArea > QWidget > QWidget {{ background-color: {couleur_fond}; }}"
        )
        self._activer_scroll_tactile()
        self._filtre_click = _FiltreAntiClickScroll(self)

    def _activer_scroll_tactile(self):
        scroller = QScroller.scroller(self.viewport())
        props = QScrollerProperties()
        props.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.2)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.MinimumVelocity, 0.05)
        scroller.setScrollerProperties(props)
        QScroller.grabGesture(
            self.viewport(),
            QScroller.ScrollerGestureType.TouchGesture,
        )
