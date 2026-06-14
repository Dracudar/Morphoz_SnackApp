"""
Tests UI pour src/UI/main_window.py (MainWindow).

Les sous-widgets lourds (InterfacePrincipaleWidget, SuiviExterieurWindow) sont
remplacés par des faux widgets Qt pour isoler la fenêtre principale.
"""

import pytest
from unittest.mock import patch
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QWidget, QMainWindow


# ── Faux widgets de remplacement ─────────────────────────────────────────────

class FakeInterface(QWidget):
    action_app_demande = Signal(str)

    def maj_etat_volet(self, cle, val):
        pass

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


# ── Barre de menus ────────────────────────────────────────────────────────────

class TestBarreMenus:
    def test_barre_menus_masquee(self, main_window):
        """La navigation est gérée par le volet tactile — la barre de menus Qt est masquée."""
        assert not main_window.menuBar().isVisible()


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


# ── Actions applicatives (volet de navigation) ────────────────────────────────

class TestActionsApp:
    def test_action_fullscreen_active_plein_ecran(self, main_window):
        assert not main_window.isFullScreen()
        main_window._on_action_app("fullscreen")
        assert main_window.isFullScreen()

    def test_action_fullscreen_inverse_etat_si_deja_actif(self, main_window):
        main_window.showFullScreen()
        main_window._on_action_app("fullscreen")
        assert not main_window.isFullScreen()

    def test_action_suivi_ext_toggle_ne_leve_pas_d_erreur(self, main_window):
        main_window._on_action_app("suivi_ext_toggle")

    def test_action_inconnue_ignoree(self, main_window):
        main_window._on_action_app("action_inexistante")
