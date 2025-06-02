'''
Module de gestion de l'affichage des commandes validées et en cours de préparation.
'''

import os
import tkinter as tk
from tkinter import ttk, messagebox

from ..backend.commandes_utils import charger_fichier_commande
from ..backend.commandes_suivi_gestion import (
    plat_prêt,
    livrer_plat
)

def affichage_commandes_validées(context, frame_droite_haut):
    """
    Met à jour dynamiquement la frame_droite_haut pour afficher les plats en préparation
    et prêts à être livrés, avec tri et gestion des boutons d'action.
    """
    # Charger tous les fichiers de commandes dans le dossier "en_cours"
    commandes_path = os.path.join(context.paths["archive"], "commandes", "en_cours")
    fichiers_commandes = [
        f for f in os.listdir(commandes_path)
        if f.endswith(".json") and os.path.isfile(os.path.join(commandes_path, f))
    ]

    # Effacer le contenu actuel de la frame
    for widget in frame_droite_haut.winfo_children():
        widget.destroy()

    # Vérifier s'il n'y a aucun fichier de commande
    if not fichiers_commandes:
        ttk.Label(
            frame_droite_haut,
            text="Aucun plat en préparation !",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 14, "bold")
        ).pack(padx=10, pady=10)
        return

    # Charger et trier les plats par statut et ID
    plats_prets = []
    plats_en_preparation = []

    for fichier in fichiers_commandes:
        chemin_fichier = os.path.join(commandes_path, fichier)
        commande_data = charger_fichier_commande(chemin_fichier)

        if not commande_data:
            continue

        commande_id = commande_data["Informations"]["ID"]  # Récupérer l'ID de la commande
        for plat_id, plat in commande_data["Commande"].items():
            # Ajouter l'ID complet du plat (commande_id + plat_id)
            id_complet = f"{commande_id}-{plat_id.split('#')[-1]}"
            if plat["Statut"] == "Prêt":
                plats_prets.append((id_complet, plat, chemin_fichier))
            elif plat["Statut"] == "En préparation":
                plats_en_preparation.append((id_complet, plat, chemin_fichier))

    # Trier les plats par ID
    plats_prets.sort(key=lambda x: x[0])
    plats_en_preparation.sort(key=lambda x: x[0])

    # Fusionner les listes pour l'affichage
    plats_a_afficher = plats_prets + plats_en_preparation

    # Ajouter un titre dynamique avec le nombre de plats affichés
    ttk.Label(
        frame_droite_haut,
        text=f"Plats en préparations : {len(plats_a_afficher)}",
        style="TLabel",
        background="#2b2b2b",
        foreground="white",
        font=("Cambria", 14, "bold")
    ).pack(padx=10, pady=10)

    # Ajouter une barre de défilement si nécessaire
    canvas = tk.Canvas(frame_droite_haut, bg="#2b2b2b")
    scrollbar = ttk.Scrollbar(frame_droite_haut, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, style="TFrame")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Afficher les plats
    for id_complet, plat, chemin_fichier in plats_a_afficher:
        frame_plat = ttk.Frame(scrollable_frame, style="TFrame")
        frame_plat.pack(fill="x", padx=10, pady=5)

        # Afficher l'ID complet et le nom du plat
        ttk.Label(
            frame_plat,
            text=f"{id_complet}\n{plat['Nom']}",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 12)
        ).pack(side="left", padx=5)

        # Ajouter un bouton selon le statut
        if plat["Statut"] == "Prêt":
            ttk.Button(
                frame_plat,
                text="Livrer",
                command=lambda p_id=id_complet, cf=chemin_fichier: livrer_plat(cf, p_id, affichage_commandes_validées, context, frame_droite_haut),
                style="TButton"
            ).pack(side="right", padx=5)
        elif plat["Statut"] == "En préparation":
            ttk.Button(
                frame_plat,
                text="Prêt",
                command=lambda p_id=id_complet, cf=chemin_fichier: plat_prêt(cf, p_id, affichage_commandes_validées, context, frame_droite_haut),
                style="TButton"
            ).pack(side="right", padx=5)
