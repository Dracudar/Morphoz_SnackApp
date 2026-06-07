#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window.py - Main Window Module

Description:
    This module contains the main window implementation for the Morphoz SnackApp UI.

Author :
    Dracudar

Version:
    2.1

Date de création :
    2026.05.12

Date de modification:
    2026.06.08
"""

# Importation des modules nécessaires
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow

from src.UI.view.interface_principale import InterfacePrincipaleWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre
        self.setWindowTitle("Morphoz SnackApp")
        self.setGeometry(100, 100, 1200, 800)

        # Créer le widget central
        self.interface_widget = InterfacePrincipaleWidget()
        self.setCentralWidget(self.interface_widget)

        # Initialiser les actions et les menus
        self.setup_shortcuts()
        self.setup_menus()
    
    def setup_shortcuts(self):
        """Configure les actions globales de la fenêtre."""

        self.quit_action = QAction("Quitter", self)
        self.quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.quit_action.triggered.connect(self.close)
        self.addAction(self.quit_action)

        self.fullscreen_action = QAction("Plein écran", self)
        self.fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_F11))
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.addAction(self.fullscreen_action)

        self.exit_fullscreen_action = QAction("Quitter le plein écran", self)
        self.exit_fullscreen_action.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        self.exit_fullscreen_action.triggered.connect(self.exit_fullscreen)
        self.addAction(self.exit_fullscreen_action)

        self.minimize_action = QAction("Minimiser", self)
        self.minimize_action.setShortcut(QKeySequence("Ctrl+M"))
        self.minimize_action.triggered.connect(self.showMinimized)
        self.addAction(self.minimize_action)
    
    def setup_menus(self):
        """Configure les menus"""
        menubar = self.menuBar()
        
        # Menu Application
        app_menu = menubar.addMenu("&App")

        
        self.fullscreen_action.setCheckable(True)
        app_menu.addAction(self.fullscreen_action)
        app_menu.addAction(self.quit_action)
        
        # Menu Affichage
        view_menu = menubar.addMenu("&Affichage")

        self.saisie_action = QAction("Saisie Commande", self)
        self.saisie_action.triggered.connect(lambda: self.interface_widget.set_left_page("saisie"))

        self.stock_action = QAction("Fenetre Stock", self)
        self.stock_action.triggered.connect(lambda: self.interface_widget.set_left_page("stock"))

        self.carte_action = QAction("Fenetre Carte", self)
        self.carte_action.triggered.connect(lambda: self.interface_widget.set_left_page("carte"))

        self.historique_action = QAction("Historique", self)
        self.historique_action.triggered.connect(lambda: self.interface_widget.set_left_page("historique"))

        self.parametres_action = QAction("Parametres", self)
        self.parametres_action.triggered.connect(
            lambda: self.interface_widget.set_left_page("parametres")
        )

        self.poste_prep_action = QAction("Poste de préparation", self)
        self.poste_prep_action.triggered.connect(
            lambda: self.interface_widget.set_left_page("poste_preparation")
        )

        view_menu.addAction(self.saisie_action)
        view_menu.addAction(self.poste_prep_action)
        view_menu.addSeparator()
        view_menu.addAction(self.carte_action)
        view_menu.addAction(self.stock_action)
        view_menu.addAction(self.historique_action)
        view_menu.addSeparator()
        view_menu.addAction(self.parametres_action)
        
    
    def toggle_fullscreen(self):
        """Bascule le mode plein écran"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def exit_fullscreen(self):
        """Quitte le plein écran"""
        if self.isFullScreen():
            self.showNormal()
