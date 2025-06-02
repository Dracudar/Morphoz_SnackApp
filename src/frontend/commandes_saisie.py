'''
Module d'affichage de la commande actuelle en cours de saisie
'''

import os
from tkinter import ttk, messagebox

from ..backend.commandes_utils import charger_fichier_commande
from ..backend.commandes_saisie_gestion import (
    annuler_plat,
    valider_commande
)

def affichage_commande_actuelle(context, frame_gauche_bas, frame_droite_haut):
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

    # Vérifier si aucun fichier de commande n'est présent
    if not fichiers_commandes:
        # Effacer le contenu actuel de la frame
        for widget in frame_gauche_bas.winfo_children():
            widget.destroy()

        ttk.Label(
            frame_gauche_bas,
            text="Aucune commande en cours...",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 14, "bold")
        ).pack(padx=10, pady=10)
        return

    # Vérifier s'il y a plus d'un fichier de commande
    if len(fichiers_commandes) > 1:
        messagebox.showerror(
            "Erreur",
            "Le dossier 'commandes' doit contenir exactement un fichier JSON actif."
        )
        return

    # Charger le fichier de commande
    commande_file = os.path.join(commandes_path, fichiers_commandes[0])
    commande_data = charger_fichier_commande(commande_file)

    if not commande_data:
        messagebox.showerror("Erreur", "Impossible de charger la commande en cours.")
        return

    # Effacer le contenu actuel de la frame
    for widget in frame_gauche_bas.winfo_children():
        widget.destroy()

    # Titre de la frame
    ttk.Label(
        frame_gauche_bas,
        text=f"Récapitulatif de la commande {commande_data['Informations']['ID']}",
        style="TLabel",
        background="#2b2b2b",
        foreground="white",
        font=("Cambria", 14, "bold")
    ).pack(padx=10, pady=10)

    # Affichage des plats en attente
    for plat_id, plat in commande_data["Commande"].items():
        if plat["Statut"] == "En attente":
            frame_plat = ttk.Frame(frame_gauche_bas, style="TFrame")
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
                command=lambda p_id=plat_id: annuler_plat(commande_file, p_id, commande_file, affichage_commande_actuelle, context, frame_gauche_bas)
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
        frame_gauche_bas,
        text=f"Montant total : {montant_total:.2f} €",
        style="TLabel",
        background="#2b2b2b",
        foreground="white",
        font=("Cambria", 12, "bold")
    ).pack(pady=10)

    # Bouton pour valider la commande

    from ..frontend.commandes_suivi import affichage_commandes_validées
    ttk.Button(
        frame_gauche_bas,
        text="Valider la commande",
        command=lambda: valider_commande(context, commande_file, affichage_commande_actuelle, frame_gauche_bas, affichage_commandes_validées, frame_droite_haut),
        style="TButton"
    ).pack(pady=10) # TODO : lorsque l'affichage_commandes_validées sera de nouveau fonctionnel, il faudra l'appeler ici