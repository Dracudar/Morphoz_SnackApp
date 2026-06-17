#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_tactile.py

Description:
    Tests UI pour src/utils/tactile.py.
    Couvre ScrollAreaTactile, BoutonTactile et EnTeteCliquable.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.14

Date de modification:
    2026.06.14
"""

import pytest
from PySide6.QtCore import Qt, QEvent, QPointF
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QPushButton, QFrame, QWidget, QScroller

from src.utils.tactile import (
    BoutonIngredientTactile,
    BoutonTactile,
    EnTeteCliquable,
    ScrollAreaTactile,
)


def _make_mouse_event(btn: Qt.MouseButton = Qt.MouseButton.LeftButton) -> QMouseEvent:
    """Construit un QMouseEvent de type MouseButtonRelease minimal."""
    return QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(0, 0),
        QPointF(0, 0),
        btn,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )


@pytest.fixture
def scroll_area(qtbot):
    sa = ScrollAreaTactile()
    qtbot.addWidget(sa)
    return sa


# ── ScrollAreaTactile ─────────────────────────────────────────────────────────

class TestScrollAreaTactile:
    def test_scrollbar_verticale_masquee(self, scroll_area):
        assert scroll_area.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    def test_scrollbar_horizontale_masquee(self, scroll_area):
        assert scroll_area.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    def test_widget_resizable(self, scroll_area):
        assert scroll_area.widgetResizable() is True

    def test_pas_de_cadre(self, scroll_area):
        assert scroll_area.frameShape() == QFrame.Shape.NoFrame

    def test_couleur_fond_defaut_dans_stylesheet(self, scroll_area):
        assert "#2f3136" in scroll_area.styleSheet()

    def test_couleur_fond_personnalisee(self, qtbot):
        sa = ScrollAreaTactile(couleur_fond="#1a1a2e")
        qtbot.addWidget(sa)
        assert "#1a1a2e" in sa.styleSheet()

    def test_pas_en_scroll_initialement(self, scroll_area):
        assert scroll_area.est_en_scroll() is False

    def test_en_scroll_pendant_dragging(self, scroll_area):
        scroll_area._on_etat_scroller(QScroller.State.Dragging)
        assert scroll_area.est_en_scroll() is True

    def test_timer_demarre_apres_inactive(self, scroll_area):
        scroll_area._en_scroll = True
        scroll_area._on_etat_scroller(QScroller.State.Inactive)
        assert scroll_area._timer_reset_scroll.isActive()

    def test_timer_stoppe_quand_drag_reprend(self, scroll_area):
        scroll_area._timer_reset_scroll.start()
        scroll_area._on_etat_scroller(QScroller.State.Dragging)
        assert not scroll_area._timer_reset_scroll.isActive()

    def test_reset_scroll_desactive_flag(self, scroll_area):
        scroll_area._en_scroll = True
        scroll_area._reset_scroll()
        assert scroll_area.est_en_scroll() is False

    def test_inactive_sans_drag_prealable_pas_de_timer(self, scroll_area):
        """Inactive sans drag préalable ne doit pas démarrer le timer."""
        scroll_area._en_scroll = False
        scroll_area._on_etat_scroller(QScroller.State.Inactive)
        assert not scroll_area._timer_reset_scroll.isActive()


# ── BoutonTactile ─────────────────────────────────────────────────────────────

class TestBoutonTactile:
    def test_cree_avec_texte(self, scroll_area, qtbot):
        btn = BoutonTactile("Mozzarella", scroll_area)
        qtbot.addWidget(btn)
        assert btn.text() == "Mozzarella"

    def test_reference_scroll_area_conservee(self, scroll_area, qtbot):
        btn = BoutonTactile("OK", scroll_area)
        qtbot.addWidget(btn)
        assert btn._scroll_area is scroll_area

    def test_release_bloque_si_scroll_actif(self, scroll_area, qtbot, monkeypatch):
        """mouseReleaseEvent doit court-circuiter le parent quand le scroll est en cours."""
        scroll_area._en_scroll = True
        btn = BoutonTactile("OK", scroll_area)
        qtbot.addWidget(btn)

        appele = []
        monkeypatch.setattr(QPushButton, "mouseReleaseEvent", lambda self, e: appele.append(True))

        btn.mouseReleaseEvent(_make_mouse_event())
        assert appele == []

    def test_release_propage_si_pas_de_scroll(self, scroll_area, qtbot, monkeypatch):
        """mouseReleaseEvent doit appeler le parent quand aucun scroll n'est en cours."""
        scroll_area._en_scroll = False
        btn = BoutonTactile("OK", scroll_area)
        qtbot.addWidget(btn)

        appele = []
        monkeypatch.setattr(QPushButton, "mouseReleaseEvent", lambda self, e: appele.append(True))

        btn.mouseReleaseEvent(_make_mouse_event())
        assert len(appele) == 1

    def test_alias_bouton_ingredient(self):
        assert BoutonIngredientTactile is BoutonTactile


# ── EnTeteCliquable ───────────────────────────────────────────────────────────

class TestEnTeteCliquable:
    def test_curseur_main(self, qtbot):
        entete = EnTeteCliquable()
        qtbot.addWidget(entete)
        assert entete.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_signal_clicked_emis_sans_parent_scroll(self, qtbot):
        """Sans parent ScrollAreaTactile, clicked est toujours émis."""
        entete = EnTeteCliquable()
        qtbot.addWidget(entete)

        recus = []
        entete.clicked.connect(lambda: recus.append(True))
        entete.mouseReleaseEvent(_make_mouse_event())

        assert len(recus) == 1

    def test_signal_non_emis_clic_droit(self, qtbot):
        entete = EnTeteCliquable()
        qtbot.addWidget(entete)

        recus = []
        entete.clicked.connect(lambda: recus.append(True))
        entete.mouseReleaseEvent(_make_mouse_event(Qt.MouseButton.RightButton))

        assert recus == []

    def test_signal_emis_quand_scroll_inactif(self, scroll_area, qtbot):
        conteneur = QWidget()
        scroll_area.setWidget(conteneur)
        entete = EnTeteCliquable(conteneur)
        scroll_area._en_scroll = False

        recus = []
        entete.clicked.connect(lambda: recus.append(True))
        entete.mouseReleaseEvent(_make_mouse_event())

        assert len(recus) == 1

    def test_signal_bloque_quand_scroll_actif(self, scroll_area, qtbot):
        conteneur = QWidget()
        scroll_area.setWidget(conteneur)
        entete = EnTeteCliquable(conteneur)
        scroll_area._en_scroll = True

        recus = []
        entete.clicked.connect(lambda: recus.append(True))
        entete.mouseReleaseEvent(_make_mouse_event())

        assert recus == []

    def test_chercher_scroll_area_retourne_none_sans_parent(self, qtbot):
        entete = EnTeteCliquable()
        qtbot.addWidget(entete)
        assert entete._chercher_scroll_area() is None

    def test_chercher_scroll_area_trouve_dans_hierarchie(self, scroll_area, qtbot):
        """La méthode doit remonter la hiérarchie jusqu'à trouver la ScrollAreaTactile."""
        conteneur = QWidget()
        scroll_area.setWidget(conteneur)
        entete = EnTeteCliquable(conteneur)
        assert entete._chercher_scroll_area() is scroll_area
