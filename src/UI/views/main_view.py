from tkinter import ttk

from ..styles import configurer_styles
#from ...frontend.boutons_menu import affichage_menu


def render_main_view(context, parent):
    """
    Affichage de l'application principale fonctionnant en plein écran.
    Permet :
    - La prise de commande
    - La mise en paiement
    - La validation des commandes prêtes
    - La gestion des stocks
    - Le changement de fichier de menu
    - La fermeture de l'application
    """
    configurer_styles()

    # === Frames === #
    # Affichage de fond
    back_frame = ttk.Frame(parent, style="TFrame", borderwidth=4, relief="solid")
    back_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Section gauche haut (x:2/3 y:3/4) : Menu
    frame_gauche_haut = ttk.Frame(back_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_gauche_haut.place(relx=0, rely=0, relwidth=2/3, relheight=1/4)

    # Section gauche bas (x:2/3 y:3/4) : Récapitulatif et paiement
    frame_gauche_bas = ttk.Frame(back_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_gauche_bas.place(relx=0, rely=1/4, relwidth=2/3, relheight=3/4)

    # Section droite haut (x:1/3 y:14/15) : Liste des plats commandés    global frame_droite_haut
    frame_droite_haut = ttk.Frame(back_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_droite_haut.place(relx=2/3, rely=0, relwidth=1/3, relheight=14/15)

    # Section droite bas (x:1/3 y:1/15)
    frame_droite_bas = ttk.Frame(back_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_droite_bas.place(relx=2/3, rely=14/15, relwidth=1/3, relheight=1/15)

    
    #affichage_menu(frame_gauche_haut, context)








'''

    ttk.Label(back_frame, text="Menu principal", font=("Cambria", 20)).pack(pady=20)
    try:
        menu_data = charger_donnees_menu(get_menu_file_path().get())
    except Exception as e:
        ttk.Label(back_frame, text=f"Erreur de chargement du menu : {e}").pack()
        return
    frame_boutons = ttk.Frame(back_frame)
    frame_boutons.pack()
    for plat in menu_data:
        ttk.Button(frame_boutons, text=plat, command=lambda p=plat: print(f"Plat choisi : {p}")).pack(side="left", padx=10)
    ttk.Button(back_frame, text="Retour à l'accueil", command=lambda: __retour_init(context)).pack(pady=20)

def __retour_init(context):
    from ..ui_utils import show_view
    show_view(context, "init")

'''