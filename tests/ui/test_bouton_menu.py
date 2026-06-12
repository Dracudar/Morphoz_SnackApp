"""
Tests UI pour src/modules/commandes_saisie/UI/widgets/bouton_menu.py (BoutonMenu).
"""

import pytest
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from src.modules.commandes_saisie.UI.widgets.bouton_menu import BoutonMenu


@pytest.fixture
def bouton(qtbot):
    """Crée un BoutonMenu avec une icône mockée pour éviter les accès disque."""
    with patch.object(BoutonMenu, "_load_svg_icon") as mock_icon:
        from PySide6.QtGui import QPixmap
        mock_icon.return_value = QPixmap(80, 80)
        b = BoutonMenu("Pizza", svg_path=None)
        qtbot.addWidget(b)
        return b


# ── Rendu et structure ────────────────────────────────────────────────────────

class TestBoutonMenu:
    def test_taille_fixe(self, bouton):
        assert bouton.width() == 120
        assert bouton.height() == 120

    def test_nom_categorie(self, bouton):
        assert bouton.category_name == "Pizza"

    def test_curseur_main(self, bouton):
        assert bouton.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_contient_label_nom(self, bouton):
        labels = bouton.findChildren(QLabel)
        textes = [lbl.text() for lbl in labels]
        assert "Pizza" in textes

    def test_style_applique(self, bouton):
        assert bouton.styleSheet() != ""

    def test_label_wrapping_actif(self, bouton):
        labels = [lbl for lbl in bouton.findChildren(QLabel) if lbl.text() == "Pizza"]
        assert labels[0].wordWrap() is True

    def test_label_centre(self, bouton):
        labels = [lbl for lbl in bouton.findChildren(QLabel) if lbl.text() == "Pizza"]
        assert labels[0].alignment() == Qt.AlignCenter


class TestBoutonMenuCategories:
    @pytest.mark.parametrize("nom", ["Grillade", "Salade composée", "Crêpe", "Frites"])
    def test_cree_sans_erreur(self, qtbot, nom):
        with patch.object(BoutonMenu, "_load_svg_icon") as mock_icon:
            from PySide6.QtGui import QPixmap
            mock_icon.return_value = QPixmap(80, 80)
            b = BoutonMenu(nom)
            qtbot.addWidget(b)
            assert b.category_name == nom
