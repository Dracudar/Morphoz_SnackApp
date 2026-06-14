"""
Tests UI pour src/UI/main_window.py (MainWindow).

Les sous-widgets lourds (InterfacePrincipaleWidget, SuiviExterieurWindow) sont
remplacés par des faux widgets Qt pour isoler la fenêtre principale.
"""

import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QWidget, QMainWindow


# ── Faux widgets de remplacement ─────────────────────────────────────────────

class FakeInterface(QWidget):
    def set_left_page(self, page):
        pass


class FakeSuiviWindow(QMainWindow):
    closed = Signal()

    def show(self):
        pass

    def hide(self):
        pass

    def raise_(self):
        pass

    def force_close(self):
        pass


# ── Fixture fenêtre principale ────────────────────────────────────────────────

@pytest.fixture
def main_window(qtbot, monkeypatch):
    monkeypatch.setattr("src.backend.logger.log", lambda *a, **kw: None)
    with patch("src.UI.main_window.InterfacePrincipaleWidget", FakeInterface), \
         patch("src.UI.main_window.SuiviExterieurWindow", FakeSuiviWindow):
        from src.UI.main_window import MainWindow
        window = MainWindow()
        qtbot.addWidget(window)
        return window


# ── Titre et géométrie ────────────────────────────────────────────────────────

class TestFenetrePrincipale:
    def test_titre(self, main_window):
        assert main_window.windowTitle() == "Morphoz SnackApp"

    def test_taille_initiale(self, main_window):
        assert main_window.width() == 1200
        assert main_window.height() == 800

    def test_widget_central_present(self, main_window):
        assert main_window.centralWidget() is not None


# ── Raccourcis clavier ────────────────────────────────────────────────────────

class TestRaccourcis:
    def test_raccourci_quitter(self, main_window):
        assert main_window.quit_action.shortcut() == QKeySequence("Ctrl+Q")

    def test_raccourci_plein_ecran(self, main_window):
        assert main_window.fullscreen_action.shortcut() == QKeySequence(Qt.Key.Key_F11)

    def test_raccourci_minimiser(self, main_window):
        assert main_window.minimize_action.shortcut() == QKeySequence("Ctrl+M")

    def test_raccourci_quitter_plein_ecran(self, main_window):
        assert main_window.exit_fullscreen_action.shortcut() == QKeySequence(Qt.Key.Key_Escape)


# ── Menus ─────────────────────────────────────────────────────────────────────

class TestMenus:
    def _noms_menus(self, main_window):
        mb = main_window.menuBar()
        return [mb.actions()[i].text() for i in range(len(mb.actions()))]

    def test_menu_app_present(self, main_window):
        noms = self._noms_menus(main_window)
        assert "&App" in noms

    def test_menu_affichage_present(self, main_window):
        noms = self._noms_menus(main_window)
        assert "&Affichage" in noms

    def test_actions_affichage(self, main_window):
        assert hasattr(main_window, "saisie_action")
        assert hasattr(main_window, "stock_action")
        assert hasattr(main_window, "carte_action")
        assert hasattr(main_window, "historique_action")
        assert hasattr(main_window, "parametres_action")
        assert hasattr(main_window, "poste_prep_action")
        assert hasattr(main_window, "suivi_ext_action")
        assert hasattr(main_window, "logs_action")

    def test_action_affichage_exterieur_cochable(self, main_window):
        assert main_window.suivi_ext_action.isCheckable() is True

    def test_action_plein_ecran_cochable(self, main_window):
        assert main_window.fullscreen_action.isCheckable() is True


# ── Plein écran ───────────────────────────────────────────────────────────────

class TestPleinEcran:
    def test_toggle_active_plein_ecran(self, main_window, qtbot):
        assert not main_window.isFullScreen()
        main_window.toggle_fullscreen()
        assert main_window.isFullScreen()

    def test_toggle_desactive_plein_ecran(self, main_window, qtbot):
        main_window.toggle_fullscreen()
        main_window.toggle_fullscreen()
        assert not main_window.isFullScreen()

    def test_exit_fullscreen_depuis_plein_ecran(self, main_window):
        main_window.showFullScreen()
        main_window.exit_fullscreen()
        assert not main_window.isFullScreen()

    def test_exit_fullscreen_sans_effet_si_normal(self, main_window):
        main_window.exit_fullscreen()
        assert not main_window.isFullScreen()
