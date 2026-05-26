from tkinter import ttk
from ..styles import configurer_styles
from ...backend.gestion_stock import StockCache

images_references = []  # Liste pour stocker les références des images

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

    # === Initialisation du cache de stock === #
    if not hasattr(context, "stock_cache"):
        context.stock_cache = StockCache(context.paths["stock"])
        # Synchroniser le cache avec les plats déjà en attente
        from ...backend.commandes_utils import charger_fichier_commande
        import os
        commandes_path = os.path.join(context.paths["archive"], "commandes")
        fichiers_commandes = [
            f for f in os.listdir(commandes_path)
            if f.endswith(".json") and os.path.isfile(os.path.join(commandes_path, f))
        ]
        if fichiers_commandes:
            chemin_fichier = os.path.join(commandes_path, fichiers_commandes[0])
            commande_data = charger_fichier_commande(chemin_fichier)
            if commande_data:
                for plat in commande_data["Commande"].values():
                    if plat["Statut"] == "En attente":
                        if plat["Plat"] == "Pizza" or plat["Plat"] == "Pizza dessert":
                            context.stock_cache.decrementer(["Plats", "Pizza", "Pâte à pizza"])
                        elif plat["Plat"] == "Grillade":
                            for viande, quantite in plat["Composition"]["Viandes"].items():
                                context.stock_cache.decrementer(["Plats", "Grillades", viande], n=quantite)
                        # Ajoute ici les autres plats à gérer si besoin

    # === Frames === #
    # Affichage de fond
    back_frame = ttk.Frame(parent, style="TFrame", borderwidth=4, relief="solid")
    back_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Section gauche haut (x:2/3 y:3/4) : Menu
    frame_gauche_haut = ttk.Frame(back_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_gauche_haut.place(relx=0, rely=0, relwidth=2/3, relheight=1/4)

    # Section gauche bas (x:2/3 y:3/4) : Commande en saisie
    frame_gauche_bas = ttk.Frame(back_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_gauche_bas.place(relx=0, rely=1/4, relwidth=2/3, relheight=3/4)

    # Section droite haut (x:1/3 y:14/15) : Liste des plats commandés
    frame_droite_haut = ttk.Frame(back_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_droite_haut.place(relx=2/3, rely=0, relwidth=1/3, relheight=14/15)

    # Section droite bas (x:1/3 y:1/15) : Boutons support
    frame_droite_bas = ttk.Frame(back_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_droite_bas.place(relx=2/3, rely=14/15, relwidth=1/3, relheight=1/15)

    # Ajout des frames dans le context
    context.frames_main = {
        "gauche_haut": frame_gauche_haut,
        "gauche_bas": frame_gauche_bas,
        "droite_haut": frame_droite_haut,
        "droite_bas": frame_droite_bas,
    }

    # === Rendu des affichages === #
    # Boutons menu
    from ...frontend.boutons_menu import affichage_menu
    affichage_menu(context, images_references)

    # Commande en saisie
    from ...frontend.commandes_saisie import affichage_commande_actuelle
    affichage_commande_actuelle(context)

    # Commandes validées
    from ...frontend.commandes_suivi import affichage_commandes_validées
    affichage_commandes_validées(context)

    # Boutons support
    from ...frontend.boutons_utilitaires import (
        bouton_exit, 
        bouton_retour
    )
    bouton_exit(context)
    bouton_retour(context)
