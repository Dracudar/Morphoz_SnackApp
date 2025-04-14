'''
Code GUI de l'application SnackApp de Morphoz
'''

#! Importer les modules nécessaires
#!! Import de fonctions externes
from utils import chercher_fichier, sauvegarder_chemins
from utils import initialiser_chemins, get_stock_file_path, get_menu_file_path
from utils import charger_logo
from styles import configurer_styles  # Importer la configuration des styles

#!! Modules pour l'interface graphique
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
root = tk.Tk()

# Initialiser les chemins
initialiser_chemins()

# Configurer les styles
configurer_styles()

#!! Arrêt de l'application
def quitter_application():
    sauvegarder_chemins(get_stock_file_path().get(), get_menu_file_path().get())  # Sauvegarder les chemins avant de quitter
    root.destroy()  # Fermer la fenêtre

#! Interfaces d'initialisation de l'app permettant la vérification des fichier JSON et leur chargement
def menu_initialisation():
    ''' Affichage permettant de choisir les fichiers JSON de stock et de menu à utiliser '''
    # === Création de la fenêtre principale ===
    ''' Cette section crée la fenêtre principale de l'application, configure son apparence et mappe des touches pour la gestion du plein écran. '''
    root.title("SnackApp Morphoz")
    root.attributes('-fullscreen', True)  # Active le mode plein écran
    root.configure(bg="#2b2b2b")  # Couleur de fond sombre
    root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))
    root.bind("<F11>", lambda event: root.attributes('-fullscreen', True))

    #!! Charger les chemins sauvegardés
    stock_file_path = get_stock_file_path()
    menu_file_path = get_menu_file_path()

    #!! Fonction pour vérifier les fichiers et passer au menu principal
    def demarrer_menu_principal():
        if not stock_file_path.get() or not menu_file_path.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner les deux fichiers JSON.")
            return
        sauvegarder_chemins(stock_file_path.get(), menu_file_path.get())  # Sauvegarder les chemins avant de passer au menu principal

        # Supprimer tous les widgets existants dans root
        for widget in root.winfo_children():
            widget.destroy()

        # Passer au menu principal
        menu_principal()

    #!! Interface utilisateur
    #!!! Bloc titre
    ttk.Label(root, text="Bienvenue dans SnackApp", font=("Cambria", 20), background="#2b2b2b", foreground="white").grid(row=0, column=0, columnspan=1, padx=10, pady=20, sticky="nsew")

    #!!! Bloc d'instructions        note: modifier pour utiliser des packs
    #!!!! Selecteur du fichier stock
    ttk.Label(root, text="Stock :", foreground="white", background="#2b2b2b", font=("Cambria", 12)).grid(row=2, column=0, padx=10, pady=10, sticky="e")
    ttk.Entry(root, textvariable=stock_file_path, width=60, font=("Cambria", 10)).grid(row=2, column=1, padx=10, pady=10)
    ttk.Button(
        root,
        text="Chercher",
        command=lambda: stock_file_path.set(chercher_fichier() or stock_file_path.get()),
        style="TButton"
    ).grid(row=2, column=2, padx=10, pady=10, sticky="e")

    #!!!! Selecteur du fichier menu
    ttk.Label(root, text="Menu :", foreground="white", background="#2b2b2b", font=("Cambria", 12)).grid(row=3, column=0, padx=10, pady=10, sticky="e")
    ttk.Entry(root, textvariable=menu_file_path, width=60, font=("Cambria", 10)).grid(row=3, column=1, padx=10, pady=10)
    ttk.Button(
        root,
        text="Chercher",
        command=lambda: menu_file_path.set(chercher_fichier() or menu_file_path.get()),
        style="TButton"
    ).grid(row=3, column=2, padx=10, pady=10, sticky="e")

    #!!! Boutons en bas
    ttk.Button(
        root,
        text="Quitter",
        command=quitter_application,
        style="TButton"
    ).grid(row=4, column=0, columnspan=1, padx=10, pady=20, sticky="nsew")
    ttk.Button(
        root,
        text="Démarrer",
        command=demarrer_menu_principal,
        style="TButton"
    ).grid(row=4, column=1, columnspan=2, padx=10, pady=20, sticky="nsew")

    # Lancer la boucle principale
    root.mainloop()

#! Interface principale de l'application
''' 
Affichage de l'application principale fonctionnant en plein écran.
Permet :
- La prise de commande
- La mise en paiement
- La validation des commandes prêtes
- La gestion des stocks
- Le changement de fichier de menu
- La fermeture de l'application
'''

def menu_principal():
    # === Création des sections ===
    # == Cadre principal ==
    frame_principal = ttk.Frame(root, style="TFrame", borderwidth=2, relief="solid")
    frame_principal.pack(fill="both", expand=True, padx=20, pady=20)

    # == Section gauche haut (x:2/3 y:3/4) : Menu ==
    frame_gauche_haut = ttk.Frame(frame_principal, style="TFrame", borderwidth=2, relief="solid")
    frame_gauche_haut.place(relx=0, rely=0, relwidth=2/3, relheight=1/4)

    # == Section gauche milieu (x:2/3 y:2/4) : Ecran de saisi ==
    frame_gauche_bas = ttk.Frame(frame_principal, style="TFrame", borderwidth=2, relief="solid")
    frame_gauche_bas.place(relx=0, rely=1/4, relwidth=2/3, relheight=2/4)

    # == Section gauche bas (x:2/3 y:1/4) : Récapitulatif et paiement ==
    frame_gauche_bas = ttk.Frame(frame_principal, style="TFrame", borderwidth=2, relief="solid")
    frame_gauche_bas.place(relx=0, rely=3/4, relwidth=2/3, relheight=1/4)

    # == Section droite haut (x:1/3 y:14/15) : Commandes en cours ==
    frame_droite_haut = ttk.Frame(frame_principal, style="TFrame", borderwidth=2, relief="solid")
    frame_droite_haut.place(relx=2/3, rely=0, relwidth=1/3, relheight=14/15)

    # == Section droite bas (x:1/3 y:1/15) ==
    frame_droite_bas = ttk.Frame(frame_principal, style="TFrame", borderwidth=2, relief="solid")
    frame_droite_bas.place(relx=2/3, rely=14/15, relwidth=1/3, relheight=1/15)

    # === Textes d'instructions ===
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
        text="Commandes en cours :\n",
        style="TLabel",
        background="#2b2b2b",
        foreground="white"
    ).pack(padx=10, pady=10)

    # === Création des boutons ===
    # == Bouton menu ==
    
    # = Bouton stock =
    # = Bouton exit =
    frame_exit = ttk.Frame(frame_droite_bas, style="TFrame",)
    frame_exit.place(relx=0.845, rely=0.1, relwidth=0.2, relheight=0.8)  # Ajuster la taille et la position de la frame

    logo_exit_tk = charger_logo("Logos/exit.png", taille=(30, 30))  # Charger le logo de sortie
    bouton_exit = ttk.Button(
        frame_exit,
        image=logo_exit_tk,
        command=quitter_application,
        style="TButton"
    )
    bouton_exit.image = logo_exit_tk  # Préserver la référence pour éviter le garbage collection
    bouton_exit.place(relx=0.5, rely=0.5, anchor="center")  # Centrer le bouton dans la frame
