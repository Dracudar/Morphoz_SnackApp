'''
Module de gestion de l'affichage des commandes validées et en cours de préparation.
'''

import os
import tkinter as tk
from tkinter import ttk, messagebox
import platform

from ..backend.commandes_utils import charger_fichier_commande
from ..backend.commandes_suivi_gestion import (
    plat_prêt,
    livrer_plat
)

def affichage_commandes_validées(context):
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
    for widget in context.frames_main["droite_haut"].winfo_children():
        widget.destroy()

    # Vérifier s'il n'y a aucun fichier de commande
    if not fichiers_commandes:
        ttk.Label(
            context.frames_main["droite_haut"],
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
        context.frames_main["droite_haut"],
        text=f"Plats en préparations : {len(plats_a_afficher)}",
        style="TLabel",
        background="#2b2b2b",
        foreground="white",
        font=("Cambria", 14, "bold")
    ).pack(padx=10, pady=10)

    def create_scrollable_canvas_local(parent, style_name="Vertical.TScrollbar", bg="#2b2b2b", ipadx=40):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            style_name, 
            background="#393e46", 
            troughcolor="#222831", 
            bordercolor="#222831", 
            arrowcolor="white",
            relief="flat",
            width=25
        )

        canvas = tk.Canvas(parent, bg=bg, highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview, style=style_name)
        scrollable_frame = ttk.Frame(canvas, style="TFrame")

        # Tag unique pour chaque canvas
        frame_tag = f"frame_{id(canvas)}"
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags=frame_tag)

        def _update_width(event):
            canvas.itemconfig(frame_tag, width=event.width)
        canvas.bind("<Configure>", _update_width)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, ipadx=ipadx)
        scrollbar.pack(side="right", fill="y")

        # --- Gestion du scroll à la molette ---
        def _on_mousewheel(event):
            first, last = canvas.yview()
            if event.delta > 0 and first <= 0:
                return
            if event.delta < 0 and last >= 1:
                return
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def _on_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        # Focus sur le canvas au survol pour activer la molette
        canvas.bind("<Enter>", lambda e: canvas.focus_set())
        if platform.system() == "Linux":
            canvas.bind("<Button-4>", _on_mousewheel_linux)
            canvas.bind("<Button-5>", _on_mousewheel_linux)
        else:
            canvas.bind("<MouseWheel>", _on_mousewheel)

        # --- Gestion du drag tactile (scroll vertical uniquement) ---
        def _on_press(event):
            canvas.scan_mark(event.x, event.y)
        def _on_drag(event):
            canvas.scan_dragto(event.x, event.y, gain=1)
            # Verrouille le scroll horizontal
            canvas.xview_moveto(0)
            canvas.update_idletasks()
            first, last = canvas.yview()
            if first < 0:
                canvas.yview_moveto(0)
            elif last > 1:
                canvas.yview_moveto(1 - (last - first))

        canvas.bind("<ButtonPress-1>", _on_press)
        canvas.bind("<B1-Motion>", _on_drag)

        return canvas, scrollable_frame

    canvas, scrollable_frame = create_scrollable_canvas_local(context.frames_main["droite_haut"])

    # Initialiser le pool de frames si besoin
    if not hasattr(context, "frames_plats_pool"):
        context.frames_main_plats_pool = []
        
    # Affichage des plats
    for i, (id_complet, plat, chemin_fichier) in enumerate(plats_a_afficher):
        # Réutilise une frame existante ou en crée une nouvelle
        if i < len(context.frames_main_plats_pool):
            frame_plat = context.frames_main_plats_pool[i]
            for widget in frame_plat.winfo_children():
                widget.destroy()
            frame_plat.pack(fill="x", padx=10, pady=5)
        else:
            frame_plat = ttk.Frame(scrollable_frame, style="TFrame")
            frame_plat.pack(fill="x", padx=10, pady=5)
            context.frames_main_plats_pool.append(frame_plat)

        # Bouton selon le statut
        if plat["Statut"] == "Prêt":
            ttk.Button(
                frame_plat,
                text="Livrer",
                command=lambda p_id=id_complet, cf=chemin_fichier: livrer_plat(context, cf, p_id, affichage_commandes_validées),
                style="TButton"
            ).pack(side="left", padx=5)
        elif plat["Statut"] == "En préparation":
            ttk.Button(
                frame_plat,
                text="Prêt",
                command=lambda p_id=id_complet, cf=chemin_fichier: plat_prêt(context, cf, p_id, affichage_commandes_validées),
                style="TButton"
            ).pack(side="left", padx=5)

        # Label du plat
        ttk.Label(
            frame_plat,
            text=f"{id_complet}\n{plat['Nom']}",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 12)
        ).pack(side="left", padx=5)

    # Cacher les frames en trop
    for j in range(len(plats_a_afficher), len(context.frames_main_plats_pool)):
        context.frames_main_plats_pool[j].pack_forget()
