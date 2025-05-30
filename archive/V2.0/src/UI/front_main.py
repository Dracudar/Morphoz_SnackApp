'''
Code UI pour l'interface principal de l'application SnackApp.

Interfaces principales :
- Choix des plats
- Récapitulatif des commandes
- Liste des plats commandés en cours de préparation
- Section de boutons support (stock, exit)
'''

# === Importer les modules nécessaires === #
# == Fonctions utilitaires et de configuration == #
from UI.styles import configurer_styles  # Importer la configuration des styles
from src.utils import (
    get_stock_file_path, 
    get_menu_file_path,
    get_archive_folder_path
    )
from src.utils import (
    charger_donnees_menu, 
    charger_img
    )
from src.back import (
    modifier_plat, 
    annuler_plat, 
    valider_commande, 
    charger_fichier_json,
    livrer_plat,
    plat_prêt
    )
from src.temp.export import fenetre_temp
from UI.ui_utils import AppContext, create_frames_structure

vpath = {
    "stock": get_stock_file_path(),
    "menu": get_menu_file_path(),
    "archive": get_archive_folder_path()
    }

# == Modules fonctionnels == #
import os  # Importer le module os pour vérifier l'existence des fichiers

# == Modules graphiques == #
from UI.front import * # Modules Tinker
from UI.front import base_frame 

# === Initialisation des variables === #
images_references = [] # Liste globale pour stocker les références des images
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
    root.bind("<Control-q>", lambda event: quitter_app())  # Quitter l'application avec Ctrl+Q

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

def quitter_app():
    """Fonction pour quitter proprement l'application."""
    root.destroy()  # Fermer la fenêtre

# === Code principal === #
def menu_principal(context: AppContext): # 2nd interface
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
    create_frames_structure(context, mode="main")

    # === Initialisation des frames === #
    frames_menu_principal(root)  # Créer les sections de l'interface principale

    # === Elements fonctionnels === #
    # == Prise de commande : Génération des boutons du menu == #
    # Titre de la frame
    ttk.Label(
        frame_gauche_haut,
        text="Menu",
        style="TLabel",
        background="#2b2b2b",
        foreground="white",
        font=("Cambria", 14, "bold")
    ).pack(padx=10, pady=10)

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
    
    # == Prise de commande : Gestion de la commande en cours == #
    def affichage_commande_actuelle():
        """
        Met à jour dynamiquement la frame_gauche_bas pour afficher les plats en attente
        et les actions associées.
        """
        # Charger le fichier de commande actif dans le dossier "commandes"
        commandes_path = os.path.join(get_archive_folder_path().get(), "commandes")
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
        commande_data = charger_fichier_json(commande_file)

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
                    command=lambda p_id=plat_id: annuler_plat(commande_file, p_id, commande_file, affichage_commande_actuelle)  # Appel à la fonction dans back.py
                ).pack(side="right", padx=5)

                # Bouton pour modifier le plat
                ttk.Button(
                    frame_plat,
                    text="Modifier",
                    command=lambda p=plat: modifier_plat(p)  # Appel à la fonction dans back.py
                ).pack(side="right", padx=5)

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
        ttk.Button(
            frame_gauche_bas,
            text="Valider la commande",
            command=lambda: valider_commande(commande_file, affichage_commande_actuelle, affichage_commandes_validées),
            style="TButton"
        ).pack(pady=10)

    affichage_commande_actuelle()

    # == Gestion des commandes validées en préparation == #
    def affichage_commandes_validées():
        """
        Met à jour dynamiquement la frame_droite_haut pour afficher les plats en préparation
        et prêts à être livrés, avec tri et gestion des boutons d'action.
        """
        # Charger tous les fichiers de commandes dans le dossier "en_cours"
        commandes_path = os.path.join(get_archive_folder_path().get(), "commandes", "en_cours")
        fichiers_commandes = [
            f for f in os.listdir(commandes_path)
            if f.endswith(".json") and os.path.isfile(os.path.join(commandes_path, f))
        ]

        # Effacer le contenu actuel de la frame
        for widget in frame_droite_haut.winfo_children():
            widget.destroy()

        # Vérifier s'il n'y a aucun fichier de commande
        if not fichiers_commandes:
            ttk.Label(
                frame_droite_haut,
                text="Aucun plat en préparation !",
                style="TLabel",
                background="#2b2b2b",
                foreground="white",
                font=("Cambria", 14, "bold")
            ).pack(padx=10, pady=10)
            return

        # Charger et trier les plats par statut et ID
        plats_prets = []
        plats_en_preparation = []

        for fichier in fichiers_commandes:
            chemin_fichier = os.path.join(commandes_path, fichier)
            commande_data = charger_fichier_json(chemin_fichier)

            if not commande_data:
                continue

            commande_id = commande_data["Informations"]["ID"]  # Récupérer l'ID de la commande
            for plat_id, plat in commande_data["Commande"].items():
                # Ajouter l'ID complet du plat (commande_id + plat_id)
                id_complet = f"{commande_id}-{plat_id.split('#')[-1]}"
                if plat["Statut"] == "Prêt":
                    plats_prets.append((id_complet, plat, chemin_fichier))
                elif plat["Statut"] == "En préparation":
                    plats_en_preparation.append((id_complet, plat, chemin_fichier))

        # Trier les plats par ID
        plats_prets.sort(key=lambda x: x[0])
        plats_en_preparation.sort(key=lambda x: x[0])

        # Fusionner les listes pour l'affichage
        plats_a_afficher = plats_prets + plats_en_preparation

        # Ajouter un titre dynamique avec le nombre de plats affichés
        ttk.Label(
            frame_droite_haut,
            text=f"Plats en préparations : {len(plats_a_afficher)}",
            style="TLabel",
            background="#2b2b2b",
            foreground="white",
            font=("Cambria", 14, "bold")
        ).pack(padx=10, pady=10)

        # Ajouter une barre de défilement si nécessaire
        canvas = tk.Canvas(frame_droite_haut, bg="#2b2b2b")
        scrollbar = ttk.Scrollbar(frame_droite_haut, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Afficher les plats
        for id_complet, plat, chemin_fichier in plats_a_afficher:
            frame_plat = ttk.Frame(scrollable_frame, style="TFrame")
            frame_plat.pack(fill="x", padx=10, pady=5)

            # Afficher l'ID complet et le nom du plat
            ttk.Label(
                frame_plat,
                text=f"{id_complet}\n{plat['Nom']}",
                style="TLabel",
                background="#2b2b2b",
                foreground="white",
                font=("Cambria", 12)
            ).pack(side="left", padx=5)

            # Ajouter un bouton selon le statut
            if plat["Statut"] == "Prêt":
                ttk.Button(
                    frame_plat,
                    text="Livrer",
                    command=lambda p_id=id_complet: livrer_plat(chemin_fichier, p_id, affichage_commandes_validées),
                    style="TButton"
                ).pack(side="right", padx=5)
            elif plat["Statut"] == "En préparation":
                ttk.Button(
                    frame_plat,
                    text="Prêt",
                    command=lambda p_id=id_complet: plat_prêt(chemin_fichier, p_id, affichage_commandes_validées),  # Appel à la fonction plat_pret
                    style="TButton"
                ).pack(side="right", padx=5)

    affichage_commandes_validées()

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

    # = Bouton refrech = #
    frame_refrech = ttk.Frame(frame_droite_bas, style="TFrame")
    frame_refrech.place(relx=0.2, rely=0.1, relwidth=0.2, relheight=0.8) # Positionner le bouton de refrech

    bouton_refrech = ttk.Button(
        frame_refrech,
        text="Refrech",
        command=lambda: (affichage_commande_actuelle(), affichage_commandes_validées()),  # Appeler la fonction d'affichage de la commande actuelle afin de le rafraichir 
        style="TButton"
    )
    bouton_refrech.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame

    # = Bouton exit = #
    frame_exit = ttk.Frame(frame_droite_bas, style="TFrame")
    frame_exit.place(relx=0.9, rely=0.1, relwidth=0.1, relheight=0.8) # Positionner le bouton de sortie

    logo_exit_tk = charger_img("exit.png", taille=(30, 30)) # Charger le logo de sortie
    bouton_exit = ttk.Button(
        frame_exit,
        image=logo_exit_tk,
        command=quitter_app,
        style="TButton"
    )
    images_references.append(logo_exit_tk)  # Stocker la référence
    bouton_exit.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame
