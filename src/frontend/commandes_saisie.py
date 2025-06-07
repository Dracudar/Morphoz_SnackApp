'''
Module d'affichage de la commande actuelle en cours de saisie
'''

import os
from tkinter import ttk, messagebox

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
    et les actions associées.
    """
    # Charger le fichier de commande actif dans le dossier "commandes"
    commandes_path = os.path.join(context.paths["archive"], "commandes")
    fichiers_commandes = [
        f for f in os.listdir(commandes_path)
        if f.endswith(".json") and os.path.isfile(os.path.join(commandes_path, f))
    ]

    if not fichiers_commandes: # Si aucun fichier de commande n'est trouvé
        # Effacer le contenu actuel de la frame
        for widget in context.frames["gauche_bas"].winfo_children():
            widget.destroy()

        ttk.Label(
            context.frames["gauche_bas"],
            text="Aucune commande en cours...",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 14, "bold")
        ).pack(padx=10, pady=10)
        return

    if len(fichiers_commandes) > 1:  # Si plusieurs fichiers de commande sont trouvés
        # Effacer le contenu actuel de la frame
        for widget in context.frames["gauche_bas"].winfo_children():
            widget.destroy()

        # Afficher un message d'erreur et de consigne
        ttk.Label(
            context.frames["gauche_bas"],
            text="Le dossier 'commandes' doit contenir un seul fichier JSON.\n Veuillez retirer les fichiers inutiles puis rafraîchir l'affichage.",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 14, "bold")
        ).pack(padx=10, pady=10)
        return

    if len(fichiers_commandes) == 1:  # Si un seul fichier de commande est trouvé
        # Charger le fichier de commande
        chemin_fichier = os.path.join(commandes_path, fichiers_commandes[0])
        commande_data = charger_fichier_commande(chemin_fichier)

        if not commande_data:
            messagebox.showerror("Erreur", "Impossible de charger la commande en cours.")
            return

        # Effacer le contenu actuel de la frame
        for widget in context.frames["gauche_bas"].winfo_children():
            widget.destroy()

        # Sépare la frame en trois parties
        frame_titre = ttk.Frame(context.frames["gauche_bas"], style="TFrame")
        frame_titre.place(relx=0, rely=0, relwidth=1, relheight=4/45)
        frame_plats = ttk.Frame(context.frames["gauche_bas"], style="TFrame")
        frame_plats.place(relx=0, rely=4/45, relwidth=1, relheight=34/45)
        frame_montant = ttk.Frame(context.frames["gauche_bas"], style="TFrame")
        frame_montant.place(relx=0, rely=38/45, relwidth=1, relheight=3/45)
        frame_boutons = ttk.Frame(context.frames["gauche_bas"], style="TFrame")
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

        # Affichage des plats en attente
        for plat_id, plat in commande_data["Commande"].items():
            if plat["Statut"] == "En attente":
                frame_plat = ttk.Frame(frame_plats, style="TFrame")
                frame_plat.pack(fill="x", padx=10, pady=5)

                # Numéro et nom du plat
                ttk.Label(
                    frame_plat,
                    text=f"{plat_id} - {plat['Nom']}",
                    style="TLabel",
                    background="#2b2b2b",
                    foreground="white"
                ).pack(side="left", padx=5)

                # Bouton pour annuler le plat
                ttk.Button(
                    frame_plat,
                    text="Annuler",
                    command=lambda p_id=plat_id: annuler_plat(context, chemin_fichier, p_id, affichage_commande_actuelle)
                ).pack(side="right", padx=5)

                '''
                # Bouton pour modifier le plat
                ttk.Button(
                    frame_plat,
                    text="Modifier",
                    command=lambda p=plat: modifier_plat(p)
                ).pack(side="right", padx=5)
                # TODO : Ajouter la fonctionnalité de modification de plat lorsque l'interface sera prête dans frontend/commandes_saisie_gestion.py
                '''

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
        