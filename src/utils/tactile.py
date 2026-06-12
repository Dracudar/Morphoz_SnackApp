#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tactile.py

Description:
    Composants Qt adaptés aux interfaces tactiles.

Author :
    Dracudar
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QScrollArea, QScroller, QScrollerProperties


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
