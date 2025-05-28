'''
Code UI pour l'interface d'initialisation de l'application SnackApp.

Interfaces d'initialisation :
- Sélection du fichier JSON de stock
- Sélection du fichier JSON de menu
- Sauvegarde des chemins dans un fichier de configuration
- Passage au menu principal
'''

# === Importer les modules nécessaires === #
import os
from UI.styles import configurer_styles  # Importer la configuration des styles
from src.utils import (
    chercher_fichier, 
    chercher_dossier,
    sauvegarder_chemins
    )
from src.utils import (
    initialiser_chemins,
    initialiser_dossier_archive
    )
from src.utils import (
    get_stock_file_path, 
    get_menu_file_path,
    get_archive_folder_path
    )
from UI.front import * # Modules Tinker
from UI.front import base_frame 
from UI.ui_utils import create_main_window, create_frames_structure, AppContext

# === Initialiser les variables globales === #
initialiser_chemins()  # Initialiser les chemins
configurer_styles()  # Configurer les styles de l'application

vpath = {
    "stock": get_stock_file_path(),
    "menu": get_menu_file_path(),
    "archive": get_archive_folder_path()
    }


# === Structure de l'interface === #
def frames_menu_initialisation(root): # Fonction pour créer les cadres de l'interface d'initialisation
    # Frame principale
    global main_frame_ini
    main_frame_ini = ttk.Frame(root, style="TFrame", borderwidth=4, relief="solid")
    main_frame_ini.pack(fill="both", expand=True, padx=20, pady=20)

    # Section haut (x:1 y:1/4) : Titre
    global frame_haut
    frame_haut = ttk.Frame(main_frame_ini, style="TFrame", borderwidth=4, relief="solid")
    frame_haut.place(relx=0, rely=0, relwidth=1, relheight=1/4)

    # Section milieu (x:1 y:2/4) : Sélecteur de fichiers
    global frame_milieu  
    frame_milieu = ttk.Frame(main_frame_ini, style="TFrame", borderwidth=4, relief="solid")
    frame_milieu.place(relx=0, rely=1/4, relwidth=1, relheight=2/4)

    # Section droite haut (x:1 y:1/4) : Boutons
    global frame_bas
    frame_bas = ttk.Frame(main_frame_ini, style="TFrame", borderwidth=4, relief="solid")
    frame_bas.place(relx=0, rely=3/4, relwidth=1, relheight=1/4)

# Fonction pour vérifier les fichiers et passer au menu principal
def demarrer_menu_principal(archive_folder_path):
    if not vpath["stock"].get() or not vpath["menu"].get() or not archive_folder_path:
        messagebox.showerror("Erreur", "Veuillez sélectionner les fichiers JSON et le dossier d'archivage.")
        return

    # Vérifier si les fichiers existent
    if not os.path.exists(vpath["stock"].get()):
        messagebox.showerror("Erreur", f"Le fichier de stock '{vpath['stock'].get()}' est introuvable.")
        return

    if not os.path.exists(vpath["menu"].get()):
        messagebox.showerror("Erreur", f"Le fichier de menu '{vpath['menu'].get()}' est introuvable.")
        return

    # Sauvegarder les chemins avant de passer au menu principal
    sauvegarder_chemins(vpath["stock"].get(), vpath["menu"].get(), archive_folder_path)

    # Initialiser le dossier d'archivage
    try:
        initialiser_dossier_archive()
    except ValueError as e:
        messagebox.showerror("Erreur", str(e))
        return

    for widget in root.winfo_children():  # Supprimer tous les widgets existants dans frame_principal
        widget.destroy()

    from UI.front_main import menu_principal
    menu_principal()  # Passer au menu principal

# === Code principal === #
def menu_selection(): # 1ère interface
    """
    Affichage de l'interface de sélection des fichiers JSON de stock et de menu.
    Permet :
    - La sélection des fichiers JSON de stock et de menu
    - La sauvegarde des chemins dans un fichier de configuration
    - Le passage au menu principal
    """
    # Créer la fenêtre principale et le contexte
    root = create_main_window()
    context = AppContext(root=root)
    create_frames_structure(context, mode="init")

    # Charger les chemins sauvegardés
    stock_file_path = get_stock_file_path()
    menu_file_path = get_menu_file_path()
    archive_folder_path = get_archive_folder_path()

    # === Initialisation des frames === #
    base_frame["back"]  # Créer la fenêtre principale
    frames_menu_initialisation(root)
    frame_haut = main_frame_ini.winfo_children()[0]  # Récupérer le premier frame (haut)
    frame_milieu = main_frame_ini.winfo_children()[1]  # Récupérer le premier frame (milieu)
    frame_bas = main_frame_ini.winfo_children()[2]  # Récupérer le premier frame (bas)

    # === Bloc titre dans frame_haut === #
    ttk.Label(
        frame_haut,
        text="Bienvenue dans SnackApp",
        font=("Cambria", 20),
        background="#2b2b2b",
        foreground="white"
    ).pack(pady=20)

    # === Sélecteur du fichier stock dans frame_milieu === #
    frame_stock = ttk.Frame(frame_milieu, style="TFrame")
    frame_stock.pack(fill="x", pady=10)

    ttk.Label(
        frame_stock,
        text="Stock :",
        foreground="white",
        background="#2b2b2b",
        font=("Cambria", 12)
    ).pack(side="left", padx=10)

    ttk.Entry(
        frame_stock,
        textvariable=stock_file_path,
        width=60,
        font=("Cambria", 10)
    ).pack(side="left", padx=10)

    ttk.Button(
        frame_stock,
        text="Chercher",
        command=lambda: stock_file_path.set(chercher_fichier() or stock_file_path.get()),
        style="TButton"
    ).pack(side="left", padx=10)

    # === Sélecteur du fichier menu dans frame_milieu === #
    frame_menu = ttk.Frame(frame_milieu, style="TFrame")
    frame_menu.pack(fill="x", pady=10)

    ttk.Label(
        frame_menu,
        text="Menu :",
        foreground="white",
        background="#2b2b2b",
        font=("Cambria", 12)
    ).pack(side="left", padx=10)

    ttk.Entry(
        frame_menu,
        textvariable=menu_file_path,
        width=60,
        font=("Cambria", 10)
    ).pack(side="left", padx=10)

    ttk.Button(
        frame_menu,
        text="Chercher",
        command=lambda: menu_file_path.set(chercher_fichier() or menu_file_path.get()),
        style="TButton"
    ).pack(side="left", padx=10)

    # === Sélecteur du dossier d'archivage dans frame_milieu === #
    frame_archive = ttk.Frame(frame_milieu, style="TFrame")
    frame_archive.pack(fill="x", pady=10)

    ttk.Label(
        frame_archive,
        text="Dossier d'archivage :",
        foreground="white",
        background="#2b2b2b",
        font=("Cambria", 12)
    ).pack(side="left", padx=10)

    ttk.Entry(
        frame_archive,
        textvariable=archive_folder_path,
        width=60,
        font=("Cambria", 10)
    ).pack(side="left", padx=10)

    ttk.Button(
        frame_archive,
        text="Chercher",
        command=lambda: archive_folder_path.set(chercher_dossier() or archive_folder_path.get()),
        style="TButton"
    ).pack(side="left", padx=10)

    # === Boutons en bas dans frame_bas === #
    frame_boutons = ttk.Frame(frame_bas, style="TFrame")
    frame_boutons.pack(pady=20)

    ttk.Button(
        frame_boutons,
        text="Quitter",
        command=base_frame["quitter"],
        style="TButton"
    ).pack(side="left", padx=20)

    ttk.Button(
        frame_boutons,
        text="Démarrer",
        command=lambda: demarrer_menu_principal(archive_folder_path.get()),
        style="TButton"
    ).pack(side="left", padx=20)

    # Lancer la boucle principale
    root.mainloop()