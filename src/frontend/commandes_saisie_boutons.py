"""
Création des boutons utilitaires pour les commandes en cours de saisie :
- Annuler la commande
- Paiement par carte
- Paiement par espèces
- Repas gratuit
"""

from tkinter import ttk
from ..UI.styles import configurer_styles
from ..backend.img_import import charger_img

images_references = [] # Liste globale pour stocker les références des images
configurer_styles()

def bouton_annuler_commande(context, frame_boutons_droit, chemin_fichier, affichage_commande_actuelle):
    from ..backend.commandes_saisie_gestion import annuler_all_plats
    # Bouton permetant de quitter l'application (détruit 'root')
    frame_annuler_commande = ttk.Frame(frame_boutons_droit, style="TFrame")
    frame_annuler_commande.place(relx=0, rely=0.1, relwidth=1/5, relheight=0.8) # Positionner le bouton de sortie

    logo_annuler_tk = charger_img("annuler.png", taille=(30, 30)) # Charger le logo d'annulation
    bouton_annuler = ttk.Button(
        frame_annuler_commande,
        image=logo_annuler_tk,
        command=lambda: annuler_all_plats(context, chemin_fichier, affichage_commande_actuelle),
        style="TButton"
    )
    images_references.append(logo_annuler_tk)  # Stocker la référence
    bouton_annuler.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame

def boutons_paiement(context, frame_boutons_milieu, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées):
    from ..backend.paiements import (
        paiement_carte,
        paiement_especes,
        gratuit
    )

    # Bouton repas gratuit
    frame_gratuit = ttk.Frame(frame_boutons_milieu, style="TFrame")
    frame_gratuit.place(relx=0, rely=0.1, relwidth=1/3, relheight=0.8) # Positionner le bouton de sortie

    logo_free_tk = charger_img("free.png", taille=(30, 30)) # Charger le logo de paiement
    bouton_paiement = ttk.Button(
        frame_gratuit,
        image=logo_free_tk,
        text="  Gratuit",
        compound="left",
        command=lambda: gratuit(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées),
        style="TButton"
    )
    images_references.append(logo_free_tk)  # Stocker la référence
    bouton_paiement.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame

    # Bouton paiement par carte
    frame_paiement_carte = ttk.Frame(frame_boutons_milieu, style="TFrame")
    frame_paiement_carte.place(relx=1/3, rely=0.1, relwidth=1/3, relheight=0.8) # Positionner le bouton de sortie

    logo_carte_tk = charger_img("CB.png", taille=(30, 30)) # Charger le logo de paiement
    bouton_paiement = ttk.Button(
        frame_paiement_carte,
        image=logo_carte_tk,
        text="  Carte",
        compound="left",
        command=lambda: paiement_carte(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées),
        style="TButton"
    )
    images_references.append(logo_carte_tk)  # Stocker la référence
    bouton_paiement.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame

    # Bouton paiement par estpèces
    frame_paiement_espece = ttk.Frame(frame_boutons_milieu, style="TFrame")
    frame_paiement_espece.place(relx=2/3, rely=0.1, relwidth=1/3, relheight=0.8) # Positionner le bouton de sortie

    logo_espece_tk = charger_img("coin.png", taille=(30, 30)) # Charger le logo de paiement
    bouton_paiement = ttk.Button(
        frame_paiement_espece,
        image=logo_espece_tk,
        text="  Espèces",
        compound="left",
        command=lambda: paiement_especes(context, chemin_fichier, affichage_commande_actuelle, affichage_commandes_validées),
        style="TButton"
    )
    images_references.append(logo_espece_tk)  # Stocker la référence
    bouton_paiement.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame