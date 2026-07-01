#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
printer_tickets_repas.py

Description:
    Impression de tickets de repas gratuits à partir d'un fichier Excel.

Author :
    Dracudar

Version:
    2.0

Date de création :
    2025.06.09

Date de modification:
    2026.06.28
"""

# Importation des modules nécessaires
from src.backend.printer import charger_logo
from escpos.printer import Usb
import pandas as pd

# Configurations
VENDOR_ID = 0x04B8
PRODUCT_ID = 0x0E15
INTERFACE = 0
MODELE = "TM-T20II"

FICHIER_CSV = r"D:\Morphoz\SnackApp_data_MS10\ticket_repas_gratuits.csv"

# Modèle de ticket de repas gratuit
def imprimer_ticket(p, logo,cat, groupe, nom, prenom, date):
    p.set(align='center')
    p.image(logo)
    p.text("\n")
    p.set(width=8, height=8)
    p.text("TICKET REPAS GRATUIT\n")
    p.text("\n")
    p.text(f"{cat}\n")
    if groupe:
        p.text(f"{groupe}\n")
    p.text("\n")
    p.text(f"{prenom} {nom}\n")
    p.text("\n")
    p.set(bold=True)
    p.text(f"Prioritaire le {date}\n")
    p.set(bold=False)
    p.text("\n" * 5)
    p.cut()

# Fonction principale pour générer les tickets de repas gratuits
def ticket_repas_gratuit():
    p = Usb(VENDOR_ID, PRODUCT_ID, INTERFACE, profile=MODELE)
    print("Connexion à l'imprimante thermique réussie.")
    p.text("\n" * 3)
    p.text("Initialisation de l'imprimante...")
    p.text("\n" * 3)
    p.cut()

    logo = charger_logo("MegaSnack.svg", taille=(500, 107))

    # Lecture du fichier CSV
    chemin = FICHIER_CSV
    df = pd.read_csv(chemin, sep=";", encoding="cp1252")
    print(df.columns.tolist())  # diagnostic temporaire

    # Vérification des colonnes nécessaires
    colonnes_requises = ["Prénom", "NOM", "Catégorie", "Groupe", "Date"]
    for col in colonnes_requises:
        if col not in df.columns:
            raise ValueError(f"La colonne '{col}' est manquante dans le fichier CSV.")

    print("Génération des tickets de repas...")
    for index, row in df.iterrows():
        nom = row["NOM"]
        prenom = row["Prénom"]
        cat = str(row["Catégorie"]).strip().lower()
        groupe = str(row["Groupe"]).strip() if pd.notna(row["Groupe"]) else ""
        date = row["Date"]

        imprimer_ticket(p, logo, cat, groupe, nom, prenom, date)

    print("Tickets de repas générés avec succès.")
    p.close()  # Fermer la connexion à l'imprimante
    print("Imprimante déconnectée.")

ticket_repas_gratuit()
