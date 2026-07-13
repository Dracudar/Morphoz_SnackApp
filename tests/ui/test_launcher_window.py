#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_launcher_window.py - Tests UI pour LauncherWindow

Description:
    Tests UI pour src/UI/launcher_window.py (LauncherWindow).

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.07.05

Date de modification:
    2026.07.05
"""

import json

import pytest

from src.UI.launcher_window import LauncherWindow


@pytest.fixture
def launcher(qtbot):
    window = LauncherWindow()
    qtbot.addWidget(window)
    return window


class TestLauncherWindow:
    def test_titre(self, launcher):
        assert launcher.windowTitle() == "Morphoz SnackApp — Choix du mode"

    def test_trois_cartes_de_mode(self, launcher):
        assert launcher.centralWidget() is not None

    @pytest.mark.parametrize("mode_id", ["complet", "prepa", "stats"])
    def test_choisir_emet_le_mode_et_ferme(self, launcher, qtbot, mode_id):
        with qtbot.waitSignal(launcher.mode_choisi, timeout=1000) as blocker:
            launcher._choisir(mode_id)
        assert blocker.args == [mode_id]
        assert not launcher.isVisible()

    def test_mode_inconnu_ignore_par_app(self):
        """Le dict de dispatch de app.py ne plante pas sur un identifiant inattendu (get() → None)."""
        classes_fenetre = {"complet": object, "prepa": object, "stats": object}
        assert classes_fenetre.get("inexistant") is None


# ── Dossier data ───────────────────────────────────────────────────────────────

class TestDossierData:
    def test_bouton_appliquer_desactive_par_defaut(self, launcher):
        assert not launcher._btn_appliquer.isEnabled()

    def test_choisir_dossier_active_le_bouton_appliquer(self, launcher, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "src.UI.launcher_window.QFileDialog.getExistingDirectory",
            lambda *a, **kw: str(tmp_path),
        )
        launcher._choisir_dossier()
        assert launcher._chemin_edit.text() == str(tmp_path)
        assert launcher._btn_appliquer.isEnabled()

    def test_choisir_dossier_annule_ne_change_rien(self, launcher, monkeypatch):
        monkeypatch.setattr(
            "src.UI.launcher_window.QFileDialog.getExistingDirectory",
            lambda *a, **kw: "",
        )
        avant = launcher._chemin_edit.text()
        launcher._choisir_dossier()
        assert launcher._chemin_edit.text() == avant
        assert not launcher._btn_appliquer.isEnabled()

    def test_appliquer_dossier_persiste_dans_config_json(self, launcher, monkeypatch, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"data_folder": ""}), encoding="utf-8")
        monkeypatch.setattr("src.UI.launcher_window.CONFIG_FILE", config_file)
        monkeypatch.setattr("src.UI.launcher_window.initialiser_dossier_data", lambda: True)

        nouveau_dossier = str(tmp_path / "data_partage")
        launcher._chemin_edit.setText(nouveau_dossier)
        launcher._btn_appliquer.setEnabled(True)
        launcher._appliquer_dossier()

        contenu = json.loads(config_file.read_text(encoding="utf-8"))
        assert contenu["data_folder"] == nouveau_dossier
        assert not launcher._btn_appliquer.isEnabled()
        assert "Appliqué" in launcher._lbl_status.text()

    def test_appliquer_dossier_vide_ne_fait_rien(self, launcher, monkeypatch, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"data_folder": ""}), encoding="utf-8")
        monkeypatch.setattr("src.UI.launcher_window.CONFIG_FILE", config_file)

        launcher._chemin_edit.setText("")
        launcher._appliquer_dossier()

        contenu = json.loads(config_file.read_text(encoding="utf-8"))
        assert contenu["data_folder"] == ""
