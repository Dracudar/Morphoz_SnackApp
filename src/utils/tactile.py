#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tactile.py

Description:
    Composants Qt adaptés aux interfaces tactiles.

Author :
    Dracudar
Modified : 2026-06-13
Version : 1.2.0
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QPushButton, QScrollArea, QScroller, QScrollerProperties


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
        self._en_scroll = False
        # Maintient _en_scroll=True un court instant après la fin du scroll pour
        # que le MouseButtonRelease synthétisé soit encore intercepté par les boutons
        self._timer_reset_scroll = QTimer(self)
        self._timer_reset_scroll.setSingleShot(True)
        self._timer_reset_scroll.setInterval(150)
        self._timer_reset_scroll.timeout.connect(self._reset_scroll)
        self._activer_scroll_tactile()

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
        scroller.stateChanged.connect(self._on_etat_scroller)

    def _on_etat_scroller(self, etat):
        if etat == QScroller.State.Dragging:
            self._en_scroll = True
            self._timer_reset_scroll.stop()
        elif etat == QScroller.State.Inactive and self._en_scroll:
            self._timer_reset_scroll.start()

    def _reset_scroll(self):
        self._en_scroll = False

    def est_en_scroll(self) -> bool:
        return self._en_scroll


class BoutonIngredientTactile(QPushButton):
    """
    QPushButton checkable qui ignore le relâchement si la ScrollAreaTactile
    parente est en train de défiler, évitant les coches involontaires au scroll.
    """

    def __init__(self, texte: str, scroll_area: ScrollAreaTactile, parent=None):
        super().__init__(texte, parent)
        self._scroll_area = scroll_area

    def mouseReleaseEvent(self, event):
        if self._scroll_area.est_en_scroll():
            return
        super().mouseReleaseEvent(event)
