#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session.py - Gestion des fenêtres principales ouvertes (launcher + modes)

Description:
    Point central pour ouvrir les fenêtres de l'application (launcher et
    modes) en gardant une référence forte sur chacune, ce qui permet d'avoir
    plusieurs fenêtres ouvertes simultanément (ex. un mode + un launcher
    supplémentaire pour ouvrir un second affichage). Utilisé au démarrage
    (src/core/app.py) et depuis le bouton "Quitter" de chaque mode, qui
    laisse choisir entre fermer, revenir au launcher, ou ouvrir une nouvelle
    session de launcher sans fermer la fenêtre courante.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.16

Date de modification:
    2026.07.16
"""

from __future__ import annotations

# Références fortes vers les fenêtres ouvertes (launcher(s) et modes), indexées
# par id() — sans cela, une fenêtre sans variable locale conservée serait
# garbage collectée par Python bien que Qt continue de l'afficher.
_fenetres_ouvertes: dict[int, object] = {}


def _conserver(fenetre) -> None:
    """Garde une référence forte sur la fenêtre jusqu'à sa destruction Qt."""
    _fenetres_ouvertes[id(fenetre)] = fenetre
    fenetre.destroyed.connect(lambda: _fenetres_ouvertes.pop(id(fenetre), None))


def lancer_mode(mode: str):
    """Ouvre la fenêtre principale du mode demandé ("complet" | "prepa" | "stats")."""
    # Import différé : chaque mode a ses propres dépendances lourdes (ex.
    # Statistiques charge reportlab.graphics et PySide6.QtCharts) — ne charger
    # que celles du mode réellement choisi évite de payer le coût des 3 modes
    # à chaque démarrage, quel que soit le choix fait.
    if mode == "complet":
        from src.UI.main_window import MainWindow as classe
    elif mode == "prepa":
        from src.UI_prep.main_window_prep import MainWindowPrep as classe
    elif mode == "stats":
        from src.UI_stats.main_window_stats import MainWindowStats as classe
    else:
        return None
    fenetre = classe()
    _conserver(fenetre)
    fenetre.show()
    return fenetre


def ouvrir_launcher():
    """Ouvre une nouvelle fenêtre de choix de mode, reliée à lancer_mode."""
    from src.UI.launcher_window import LauncherWindow

    launcher = LauncherWindow()
    launcher.mode_choisi.connect(lancer_mode)
    _conserver(launcher)
    launcher.show()
    return launcher


def gerer_fermeture(fenetre) -> None:
    """Gère le clic sur "Quitter" d'une fenêtre de mode.

    Propose de fermer, de revenir au launcher (ferme cette fenêtre et rouvre
    le launcher), ou d'ouvrir une session de launcher supplémentaire sans
    fermer la fenêtre courante (pour obtenir un second affichage). N'a aucun
    effet si l'utilisateur annule.
    """
    from src.UI.dialogs.dialogue_fermeture import demander_choix_fermeture

    choix = demander_choix_fermeture(fenetre)
    if choix == "fermer":
        fenetre.close()
    elif choix == "launcher":
        ouvrir_launcher()
        fenetre.close()
    elif choix == "nouvelle_session":
        ouvrir_launcher()
