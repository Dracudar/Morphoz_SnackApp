"""
Création des boutons utilitaires pour l'app :
- Retourner au menu d'initialisation (en cas de changement de fichier)
- Afficher la gestion des stocks
- Raffraichier les affichages
- Fermet l'application
"""

from tkinter import ttk
from ..UI.styles import configurer_styles
from ..backend.img_import import charger_img


images_references = [] # Liste globale pour stocker les références des images
configurer_styles()


def bouton_exit(frame_droite_bas, context):
    # Bouton permetant de quitter l'application (détruit 'root')
    frame_exit = ttk.Frame(frame_droite_bas, style="TFrame")
    frame_exit.place(relx=0.9, rely=0.1, relwidth=0.1, relheight=0.8) # Positionner le bouton de sortie

    logo_exit_tk = charger_img("exit.png", taille=(30, 30)) # Charger le logo de sortie
    bouton_exit = ttk.Button(
        frame_exit,
        image=logo_exit_tk,
        command=context.root.destroy,
        style="TButton"
    )
    images_references.append(logo_exit_tk)  # Stocker la référence
    bouton_exit.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame

def bouton_retour(frame_droite_bas, context):
    from ..UI.ui_utils import show_view

    frame_retour = ttk.Frame(frame_droite_bas, style="TFrame")
    frame_retour.place(relx=0, rely=0.1, relwidth=0.1, relheight=0.8)  # Positionner le bouton de retour

    logo_retour_tk = charger_img("retour.png", taille=(30, 30))  # Charger le logo de retour
    bouton_retour = ttk.Button(
        frame_retour,
        image=logo_retour_tk,
        command=lambda:show_view(context, "init"),
        style="TButton"
    )
    images_references.append(logo_retour_tk)  # Stocker la référence
    bouton_retour.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame
