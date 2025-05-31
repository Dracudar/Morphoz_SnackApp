"""
Affichage de l'interface de sélection des fichiers JSON de stock et de menu.
Permet :
    - La sélection des fichiers JSON de stock et de menu
    - La sauvegarde des chemins dans un fichier de configuration
    - Le passage au menu principal
"""

# === Imports === #
from tkinter import ttk, messagebox
import os

from ...backend.chemins_gestion import (
    get_stock_file_path,
    get_menu_file_path,
    get_archive_folder_path,
    initialiser_chemins,
    save_chemins
    )
from ...frontend.explorateurs_fichiers import (
    chercher_fichier_menu,
    chercher_fichier_stock,
    chercher_dossier
    )
from ..styles import configurer_styles

# === Fonction de rendu de l'affichage d'initialisation === #
def render_init_view(context, parent):
    """Affiche l'interface de sélection des fichiers JSON de stock et de menu ainsi que l'emplacement du dossier d'archive."""
    configurer_styles()

    # Initialiser les chemins AVEC le root du contexte
    initialiser_chemins(context.root)
    vpath = {
        "stock": get_stock_file_path(),
        "menu": get_menu_file_path(),
        "archive": get_archive_folder_path()
    }

    chercher = {
        "Menu": chercher_fichier_menu,
        "Stock": chercher_fichier_stock,
        "Dossier": chercher_dossier
    }

    def start_main_view():
        if not vpath["stock"].get() or not vpath["menu"].get() or not vpath["archive"].get():
            messagebox.showerror("Erreur", "Veuillez sélectionner tous les fichiers.")
            return
        
        # Vérifier si les fichiers existent
        if not os.path.exists(vpath["stock"].get()):
            messagebox.showerror("Erreur", f"Le fichier de stock est introuvable : {vpath['stock'].get()}")
            return

        if not os.path.exists(vpath["menu"].get()):
            messagebox.showerror("Erreur", f"Le fichier de menu est introuvable : {vpath['menu'].get()}")
            return

        if not os.path.exists(vpath["archive"].get()):
            messagebox.showerror("Erreur", f"Le dossier d'archive est introuvable : {vpath['archive'].get()}")
            return

        # Sauvegarder les chemins dans le context pour la suite
        context.paths = {
            "stock": vpath["stock"].get(),
            "menu": vpath["menu"].get(),
            "archive": vpath["archive"].get()
        }

        # Sauvegarder les chemins dans le fichier de configuration
        save_chemins["all"](vpath["stock"].get(), vpath["menu"].get(), vpath["archive"].get())

        # Initialiser le dossier d'archivage
        from ...backend.chemins_exploitation import initialiser_dossier_archive
        initialiser_dossier_archive({"archive": vpath["archive"].get()})

        # Passer à la vue principale
        from ..ui_utils import show_view
        show_view(context, "main")


    # Affichage de fond
    back_frame = ttk.Frame(parent, style="TFrame", borderwidth=4, relief="solid")
    back_frame.pack(fill="both", expand=True, padx=20, pady=20)


    # Section haut (x:1 y:1/4) : Titre
    frame_haut = ttk.Frame(back_frame, style="TFrame")
    frame_haut.place(relx=0, rely=0, relwidth=1, relheight=1/4)

    ttk.Label(frame_haut, text="Bienvenue dans SnackApp", font=("Cambria", 20)).pack(pady=20)
    

    # Section milieu (x:1 y:2/4) : Sélecteurs
    frame_milieu = ttk.Frame(back_frame, style="TFrame")
    frame_milieu.place(relx=0, rely=1/4, relwidth=1, relheight=2/4)

    # Menu
    frame_menu_title = ttk.Frame(frame_milieu)
    frame_menu_title.place(relx=0, rely=0, relwidth=2/10, relheight=1/3)
    label_menu = ttk.Label(frame_menu_title, text="Menu :")
    label_menu.pack(side="right", padx=10)

    frame_menu_champ = ttk.Frame(frame_milieu)
    frame_menu_champ.place(relx=2/10, rely=0, relwidth=6/10, relheight=1/3)
    entry_menu = ttk.Entry(frame_menu_champ, textvariable=vpath["menu"])
    entry_menu.pack(side="left", fill="x", expand=True, padx=10)

    frame_menu_bouton = ttk.Frame(frame_milieu)
    frame_menu_bouton.place(relx=8/10, rely=0, relwidth=2/10, relheight=1/3)
    bouton_menu = ttk.Button(frame_menu_bouton, text="Chercher", command=lambda: vpath["menu"].set(chercher["Menu"]() or vpath["menu"].get()))
    bouton_menu.pack(side="left", padx=10)

    # Stock
    frame_stock_title = ttk.Frame(frame_milieu)
    frame_stock_title.place(relx=0, rely=1/3, relwidth=2/10, relheight=1/3)
    label_stock = ttk.Label(frame_stock_title, text="Stock :")
    label_stock.pack(side="right", padx=10)

    frame_stock_champ = ttk.Frame(frame_milieu)
    frame_stock_champ.place(relx=2/10, rely=1/3, relwidth=6/10, relheight=1/3)
    entry_stock = ttk.Entry(frame_stock_champ, textvariable=vpath["stock"])
    entry_stock.pack(side="left", fill="x", expand=True, padx=10)

    frame_stock_bouton = ttk.Frame(frame_milieu)
    frame_stock_bouton.place(relx=8/10, rely=1/3, relwidth=2/10, relheight=1/3)
    bouton_stock = ttk.Button(frame_stock_bouton, text="Chercher", command=lambda: vpath["stock"].set(chercher["Stock"]() or vpath["stock"].get()))
    bouton_stock.pack(side="left", padx=10)

    # Archive
    frame_archive_title = ttk.Frame(frame_milieu)
    frame_archive_title.place(relx=0, rely=2/3, relwidth=2/10, relheight=1/3)
    label_archive = ttk.Label(frame_archive_title, text="Archive :")
    label_archive.pack(side="right", padx=10)

    frame_archive_champ = ttk.Frame(frame_milieu)
    frame_archive_champ.place(relx=2/10, rely=2/3, relwidth=6/10, relheight=1/3)
    entry_archive = ttk.Entry(frame_archive_champ, textvariable=vpath["archive"])
    entry_archive.pack(side="left", fill="x", expand=True, padx=10)

    frame_archive_bouton = ttk.Frame(frame_milieu)
    frame_archive_bouton.place(relx=8/10, rely=2/3, relwidth=2/10, relheight=1/3)
    bouton_archive = ttk.Button(frame_archive_bouton, text="Chercher", command=lambda: vpath["archive"].set(chercher["Dossier"]() or vpath["archive"].get()))
    bouton_archive.pack(side="left", padx=10)


    # Section droite haut (x:1 y:1/4) : Boutons
    frame_bas = ttk.Frame(back_frame, style="TFrame")
    frame_bas.place(relx=0, rely=3/4, relwidth=1, relheight=1/4)

    bouton_quitter = ttk.Button(frame_bas, text="Quitter", command=context.root.destroy)
    bouton_quitter.place(relx=1/5, rely=1/4, relwidth=1/5, relheight=1/2)
    bouton_demarrer = ttk.Button(frame_bas, text="Démarrer", command=start_main_view)
    bouton_demarrer.place(relx=3/5, rely=1/4, relwidth=1/5, relheight=1/2)
