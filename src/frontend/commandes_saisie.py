'''
Module d'affichage de la commande actuelle en cours de saisie
'''

import os
import tkinter as tk
from tkinter import ttk, messagebox
import platform

from ..backend.commandes_utils import charger_fichier_commande
from ..backend.commandes_saisie_gestion import annuler_plat
from ..frontend.commandes_suivi import affichage_commandes_validées
from ..frontend.commandes_saisie_boutons import (
    bouton_annuler_commande,
    boutons_paiement
    )

def affichage_commande_actuelle(context):
    """
    Met à jour dynamiquement la frame_gauche_bas pour afficher les plats en attente
    et les actions associées, en réutilisant les frames pour optimiser l'affichage.
    """
    import os

    commandes_path = os.path.join(context.paths["archive"], "commandes")
    fichiers_commandes = [
        f for f in os.listdir(commandes_path)
        if f.endswith(".json") and os.path.isfile(os.path.join(commandes_path, f))
    ]

    # Effacer le contenu actuel de la frame si aucune commande ou erreur
    def clear_frame():
        for widget in context.frames_main["gauche_bas"].winfo_children():
            widget.destroy()

    if not fichiers_commandes:
        clear_frame()
        ttk.Label(
            context.frames_main["gauche_bas"],
            text="Aucune commande en cours...",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 14, "bold")
        ).pack(padx=10, pady=10)
        return

    if len(fichiers_commandes) > 1:
        clear_frame()
        ttk.Label(
            context.frames_main["gauche_bas"],
            text="L'archive 'commandes' doit contenir un seul fichier JSON.\n Veuillez retirer les fichiers inutiles puis rafraîchir l'affichage.",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 14, "bold")
        ).pack(padx=10, pady=10)
        return

    # Un seul fichier de commande
    chemin_fichier = os.path.join(commandes_path, fichiers_commandes[0])
    commande_data = charger_fichier_commande(chemin_fichier)

    if not commande_data:
        messagebox.showerror("Erreur", "Impossible de charger la commande en cours.")
        return

    # Sépare la frame en quatre parties
    frame_titre = ttk.Frame(context.frames_main["gauche_bas"], style="TFrame")
    frame_titre.place(relx=0, rely=0, relwidth=1, relheight=4/45)
    frame_liste = ttk.Frame(context.frames_main["gauche_bas"], style="TFrame")
    frame_liste.place(relx=0, rely=4/45, relwidth=1, relheight=34/45)
    frame_montant = ttk.Frame(context.frames_main["gauche_bas"], style="TFrame")
    frame_montant.place(relx=0, rely=38/45, relwidth=1, relheight=3/45)
    frame_boutons = ttk.Frame(context.frames_main["gauche_bas"], style="TFrame")
    frame_boutons.place(relx=0, rely=41/45, relwidth=1, relheight=4/45)

    # Titre de la commande
    ttk.Label(
        frame_titre,
        text=f"Récapitulatif de la commande {commande_data['Informations']['ID']}",
        style="TLabel",
        background="#2b2b2b",
        foreground="white",
        font=("Cambria", 14, "bold")
    ).pack(padx=10, pady=10)

    def create_scrollable_canvas_local(parent, style_name="Saisie.Vertical.TScrollbar", bg="#2b2b2b", ipadx=40):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            style_name, 
            background="#393e46", 
            troughcolor="#222831", 
            bordercolor="#222831", 
            arrowcolor="white"
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

    canvas, scrollable_frame = create_scrollable_canvas_local(frame_liste)

    # --- Pool de frames pour les plats ---
    if not hasattr(context, "frames_plats_saisie_pool"):
        context.frames_main_plats_saisie_pool = []

    plats_en_attente = [
        (plat_id, plat)
        for plat_id, plat in commande_data["Commande"].items()
        if plat["Statut"] == "En attente"
    ]

    # Affichage des plats en attente
    for i, (plat_id, plat) in enumerate(plats_en_attente):
        # Réutilise une frame existante ou en crée une nouvelle
        if i < len(context.frames_main_plats_saisie_pool):
            frame_plat = context.frames_main_plats_saisie_pool[i]
            for widget in frame_plat.winfo_children():
                widget.destroy() 
            frame_plat.pack(fill="x", padx=10, pady=5)
        else:
            frame_plat = ttk.Frame(scrollable_frame, style="TFrame")
            frame_plat.pack(fill="x", padx=10, pady=5)
            context.frames_main_plats_saisie_pool.append(frame_plat)

        # Bouton pour annuler le plat
        ttk.Button(
            frame_plat,
            text="Annuler",
            command=lambda p_id=plat_id: annuler_plat(context, chemin_fichier, p_id, affichage_commande_actuelle)
        ).pack(side="left", padx=5)

        # Numéro et nom du plat
        ttk.Label(
            frame_plat,
            text=f"{plat_id} - {plat['Nom']}",
            style="TLabel",
            background="#2b2b2b",
            foreground="white"
        ).pack(side="left", padx=5)

    # Cache les frames en trop
    for j in range(len(plats_en_attente), len(context.frames_main_plats_saisie_pool)):
        context.frames_main_plats_saisie_pool[j].pack_forget()

    # Affichage du montant total
    montant_total = commande_data["Informations"]["Montant"]
    ttk.Label(
        frame_montant,
        text=f"Montant total : {montant_total:.2f} €",
        style="TLabel",
        background="#2b2b2b",
        foreground="white",
        font=("Cambria", 12, "bold")
    ).pack(pady=10)

    # Boutons
    frame_boutons_droit = ttk.Frame(frame_boutons, style="TFrame")
    frame_boutons_droit.place(relx=0, rely=0, relwidth=5/20, relheight=1)
    frame_boutons_milieu = ttk.Frame(frame_boutons, style="TFrame")
    frame_boutons_milieu.place(relx=5/20, rely=0, relwidth=10/20, relheight=1)
    frame_boutons_gauche = ttk.Frame(frame_boutons, style="TFrame")
    frame_boutons_gauche.place(relx=15/20, rely=0, relwidth=5/20, relheight=1)

    bouton_annuler_commande(context, frame_boutons_droit, chemin_fichier, affichage_commande_actuelle)
    boutons_paiement(context, frame_boutons_milieu, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées)
