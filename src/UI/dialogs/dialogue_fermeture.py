#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dialogue_fermeture.py - Boîte de dialogue de choix à la fermeture d'un mode

Description:
    Affiche le choix proposé par le bouton "Quitter" de chaque mode : fermer
    simplement la fenêtre, fermer et revenir au launcher, ou ouvrir une
    session de launcher supplémentaire (pour un second affichage) sans
    fermer la fenêtre courante.

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

from PySide6.QtWidgets import QMessageBox


def demander_choix_fermeture(parent) -> str | None:
    """Affiche le choix de fermeture et retourne l'action choisie.

    Retourne "fermer", "launcher" (ferme cette fenêtre et revient au
    launcher) ou "nouvelle_session" (ouvre un launcher supplémentaire sans
    fermer la fenêtre courante) ; retourne None si l'utilisateur annule.
    """
    boite = QMessageBox(parent)
    boite.setWindowTitle("Quitter")
    boite.setText("Que souhaitez-vous faire ?")
    boite.setIcon(QMessageBox.Icon.Question)

    btn_fermer = boite.addButton("Fermer", QMessageBox.ButtonRole.DestructiveRole)
    btn_launcher = boite.addButton("Revenir au launcher", QMessageBox.ButtonRole.ActionRole)
    btn_nouvelle_session = boite.addButton(
        "Nouvelle session launcher", QMessageBox.ButtonRole.ActionRole
    )
    boite.addButton("Annuler", QMessageBox.ButtonRole.RejectRole)
    boite.setDefaultButton(btn_fermer)

    boite.exec()
    clique = boite.clickedButton()
    if clique is btn_fermer:
        return "fermer"
    if clique is btn_launcher:
        return "launcher"
    if clique is btn_nouvelle_session:
        return "nouvelle_session"
    return None
