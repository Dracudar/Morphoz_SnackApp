'''
Code UI pour l'interface d'initialisation et l'interface principal de l'application SnackApp.

Interfaces d'initialisation :
- Sélection du fichier JSON de stock
- Sélection du fichier JSON de menu
- Sauvegarde des chemins dans un fichier de configuration
- Passage au menu principal

Interfaces principales :
- Choix des plats
- Récapitulatif des commandes
- Liste des plats commandés en cours de préparation
- Section de boutons support (stock, exit)
'''

# === Importer les modules nécessaires === #
# == Fonctions utilitaires et de configuration == #
from src.utils import chercher_fichier, sauvegarder_chemins
from src.utils import initialiser_chemins, get_stock_file_path, get_menu_file_path
from src.utils import charger_donnees_menu, charger_donnees_stock, charger_img
from src.styles import configurer_styles  # Importer la configuration des styles

# == Fonctions backend == #
from src.front_temp import perso_pizza  # Import de la fonction d'interface de personnalisation de la pizza
from src.front_temp import perso_grillade  # Import de la fonction d'interface de personnalisation de la grillade
from src.front_temp import perso_salade_composee  # Import de la fonction d'interface de personnalisation de la salade composée
from src.front_temp import perso_frites  # Import de la fonction d'interface de personnalisation des frites
from src.front_temp import gestion_stock  # Import de la fonction d'interface de gestion du stock

# == Modules graphiques == #
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
root = tk.Tk()

# === Initialisation des variables === #
images_references = [] # Liste globale pour stocker les références des images
initialiser_chemins() # Initialiser les chemins
configurer_styles() # Configurer les styles

# === Fonctions générales === #
def back_frame(): # Fonction pour créer le cadre principal de l'application
    """ Cette section crée la fenêtre principale de l'application, configure son apparence et mappe des touches pour la gestion du plein écran. """
    # == Configuration de la fenêtre principale == #
    global root
    root.title("SnackApp Morphoz")  # Titre de la fenêtre
    # root.iconbitmap("assets/logo.ico")  # Icône de la fenêtre -> à créer
    root.geometry("800x600")  # Taille de la fenêtre
    root.attributes('-fullscreen', True)  # Active le mode plein écran
    root.configure(bg="#2b2b2b")  # Couleur de fond sombre

    # == Mappage des touches == #
    root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False)) # Quitter le mode plein écran avec Échap
    root.bind("<F11>", lambda event: root.attributes('-fullscreen', True)) # Passer en plein écran avec F11
    root.bind("<Control-q>", lambda event: quitter_application())  # Quitter l'application avec Ctrl+Q

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


def frames_menu_principal(root): # Fonction pour créer les cadres de l'interface principale
    # Frame principale
    global main_frame
    main_frame = ttk.Frame(root, style="TFrame", borderwidth=4, relief="solid")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Section gauche haut (x:2/3 y:3/4) : Menu
    global frame_gauche_haut  
    frame_gauche_haut = ttk.Frame(main_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_gauche_haut.place(relx=0, rely=0, relwidth=2/3, relheight=1/4)

    # Section gauche bas (x:2/3 y:3/4) : Récapitulatif et paiement
    global frame_gauche_bas  
    frame_gauche_bas = ttk.Frame(main_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_gauche_bas.place(relx=0, rely=1/4, relwidth=2/3, relheight=3/4)

    # Section droite haut (x:1/3 y:14/15) : Liste des plats commandés
    global frame_droite_haut  
    frame_droite_haut = ttk.Frame(main_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_droite_haut.place(relx=2/3, rely=0, relwidth=1/3, relheight=14/15)

    # Section droite bas (x:1/3 y:1/15)
    global frame_droite_bas  
    frame_droite_bas = ttk.Frame(main_frame, style="TFrame", borderwidth=4, relief="solid")
    frame_droite_bas.place(relx=2/3, rely=14/15, relwidth=1/3, relheight=1/15)

def quitter_application(): # Fonction pour d'arrêt propre de l'application
    sauvegarder_chemins(get_stock_file_path().get(), get_menu_file_path().get())  # Sauvegarder les chemins avant de quitter
    root.destroy()  # Fermer la fenêtre

# === Code principal === #
def menu_selection(): # 1ère interface
    """
    Affichage de l'interface de sélection des fichiers JSON de stock et de menu.
    Permet :
    - La sélection des fichiers JSON de stock et de menu
    - La sauvegarde des chemins dans un fichier de configuration
    - Le passage au menu principal
    """
    # Charger les chemins sauvegardés
    stock_file_path = get_stock_file_path()
    menu_file_path = get_menu_file_path()

    # Fonction pour vérifier les fichiers et passer au menu principal
    def demarrer_menu_principal():
        if not stock_file_path.get() or not menu_file_path.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner les deux fichiers JSON.")
            return
        sauvegarder_chemins(stock_file_path.get(), menu_file_path.get())  # Sauvegarder les chemins avant de passer au menu principal

        for widget in root.winfo_children(): # Supprimer tous les widgets existants dans frame_principal
            widget.destroy()

        menu_principal() # Passer au menu principal

    # === Initialisation des frames === #
    back_frame()  # Créer la fenêtre principale
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

    # === Boutons en bas dans frame_bas === #
    frame_boutons = ttk.Frame(frame_bas, style="TFrame")
    frame_boutons.pack(pady=20)

    ttk.Button(
        frame_boutons,
        text="Quitter",
        command=quitter_application,
        style="TButton"
    ).pack(side="left", padx=20)

    ttk.Button(
        frame_boutons,
        text="Démarrer",
        command=demarrer_menu_principal,
        style="TButton"
    ).pack(side="left", padx=20)

    # Lancer la boucle principale
    root.mainloop()

def menu_principal(): # 2nd interface
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
    # === Initialisation des frames === #
    frames_menu_principal(root)  # Créer les sections de l'interface principale

    # === Elements fonctionnels === #
    # == Titres des sections == #
    ttk.Label(
        frame_gauche_haut,
        text="Menu",
        style="TLabel",
        background="#2b2b2b",
        foreground="white"
    ).pack(padx=10, pady=10)

    ttk.Label(
        frame_gauche_bas,
        text="Récapitulatif et paiement",
        style="TLabel",
        background="#2b2b2b",
        foreground="white"
    ).pack(padx=10, pady=10)

    ttk.Label(
        frame_droite_haut,
        text="Plats commandés :\n",
        style="TLabel",
        background="#2b2b2b",
        foreground="white"
    ).pack(padx=10, pady=10)

    # == Prise de commande : Génération des boutons du menu == #
    # Charger les données du fichier JSON de menu
    try:
        menu_data = charger_donnees_menu(get_menu_file_path().get())
    except (FileNotFoundError, ValueError) as e:
        messagebox.showerror("Erreur", str(e)) 
        return

    # Créer un cadre pour centrer les boutons horizontalement
    frame_boutons = ttk.Frame(frame_gauche_haut, style="TFrame")
    frame_boutons.pack(expand=True)

    # Ajouter des boutons pour chaque plat
    def structure_boutons_menu(parent, plat, logo_tk, action):
        """
        Crée un bouton avec une image et un texte (nom du plat) dans un conteneur de taille fixe.
        """
        # Créer un conteneur pour forcer une taille uniforme
        cadre_bouton = ttk.Frame(parent, width=150, height=150, style="TFrame")
        cadre_bouton.pack_propagate(False)  # Empêcher le conteneur de s'adapter à son contenu
        cadre_bouton.pack(side="left", padx=10, pady=10)

        # Ajouter le bouton dans le conteneur
        bouton = ttk.Button(
            cadre_bouton,
            text=plat,
            image=logo_tk,
            command=action,  # Appeler l'action associée au bouton
            compound="top",  # Affiche le texte en dessous de l'image
            style="TButton"
        )
        bouton.image = logo_tk  # Préserver la référence
        bouton.pack(expand=True, fill="both")  # Remplir tout l'espace du conteneur

    for plat in menu_data:
        # Charger une image pour les plats
        try:
            logo_tk = charger_img(f"{plat.lower()}.png", taille=(100, 100))
        except FileNotFoundError:
            logo_tk = charger_img("vide.png", taille=(100, 100))

        images_references.append(logo_tk)  # Stocker la référence

        # Définir l'action en fonction du plat
        if plat.lower() == "pizza":
            action = lambda: perso_pizza(root)  # Appeler la personnalisation des pizzas
        elif plat.lower() == "grillade":
            action = lambda: perso_grillade(root)  # Appeler la personnalisation des grillades
        elif plat.lower() == "salade composée":
            action = lambda: perso_salade_composee(root)  # Appeler la personnalisation des salades composées
        elif plat.lower() == "frites":
            action = lambda: perso_frites(root)  # Appeler la personnalisation des frites
        else:
            action = lambda: print(f"Plat sélectionné : {plat}")  # Action par défaut (impression dans la console)

        # Créer le bouton avec la fonction dédiée
        structure_boutons_menu(
            parent=frame_boutons,
            plat=plat,
            logo_tk=logo_tk,
            action=action
        )

    # == Actions support == #
    # = Bouton stock = #
    frame_stock = ttk.Frame(frame_droite_bas, style="TFrame")
    frame_stock.place(relx=0, rely=0.1, relwidth=0.2, relheight=0.8) # Positionner le bouton de sortie

    bouton_stock = ttk.Button(
        frame_stock,
        text="Stock",
        command=lambda: gestion_stock(root),  # Appeler la fonction de gestion du stock
        style="TButton"
    )
    bouton_stock.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame


    # = Bouton exit = #
    frame_exit = ttk.Frame(frame_droite_bas, style="TFrame")
    frame_exit.place(relx=0.9, rely=0.1, relwidth=0.1, relheight=0.8) # Positionner le bouton de sortie

    logo_exit_tk = charger_img("exit.png", taille=(30, 30)) # Charger le logo de sortie
    bouton_exit = ttk.Button(
        frame_exit,
        image=logo_exit_tk,
        command=quitter_application,
        style="TButton"
    )
    images_references.append(logo_exit_tk)  # Stocker la référence
    bouton_exit.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame
