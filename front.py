'''
Code GUI de l'application SnackApp de Morphoz
'''

#! Importer les modules nécessaires
#!! Import de fonctions externes
from utils import chercher_fichier, sauvegarder_chemins
from utils import initialiser_chemins, get_stock_file_path, get_menu_file_path
from utils import charger_logo

#!! Modules pour l'interface graphique
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
root = tk.Tk()


# Initialiser les chemins
initialiser_chemins()

#!! Arrêt de l'application
def quitter_application():
    sauvegarder_chemins(get_stock_file_path().get(), get_menu_file_path().get())  # Sauvegarder les chemins avant de quitter
    root.destroy()  # Fermer la fenêtre

#!! Configuration des styles de l'application
style = ttk.Style()
style.theme_use("clam")  # Utiliser un thème compatible avec la personnalisation

# Configuration du style pour les boutons (TButton)
style.configure(
    "TButton", 
    font=("Cambria", 12),  # Définit la police et sa taille
    relief="flat",  # Style de bouton plat pour un design moderne
    background="#444444",  # Couleur de fond sombre
    foreground="white"  # Texte en blanc pour un bon contraste
)
style.map(
    "TButton", 
    background=[("active", "#555555")]  # Changer la couleur de fond lorsque le bouton est actif (interactif)
)

# Configuration du style pour les labels (TLabel)
style.configure(
    "TLabel", 
    font=("Cambria", 12),  # Définit la police et sa taille
    background="#2b2b2b",  # Couleur de fond sombre
    foreground="white"  # Texte en blanc pour une bonne lisibilité
)

# Configuration du style pour les champs de saisie (TEntry)
style.configure(
    "TEntry", 
    font=("Cambria", 10),  # Définit la police et sa taille
    fieldbackground="#444444",  # Couleur de fond sombre
    foreground="white"  # Texte en blanc pour un bon contraste
)

# Configuration du style pour les cadres / conteneurs principaux (TFrame)
style.configure(
    "TFrame", 
    background="#2b2b2b"  # Couleur de fond sombre
)

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
    # Cadre principal
    frame_principal = ttk.Frame(root, style="TFrame")
    frame_principal.pack(fill="both", expand=True, padx=20, pady=20)

    # === Section gauche (2/3) ===
    frame_gauche = ttk.Frame(frame_principal, style="TFrame", borderwidth=2, relief="solid")
    frame_gauche.place(relx=0, rely=0, relwidth=2/3, relheight=1)

    # == Sous-section gauche haut (3/4) ==
    frame_gauche_haut = ttk.Frame(frame_gauche, style="TFrame", borderwidth=2, relief="solid")
    frame_gauche_haut.place(relx=0, rely=0, relwidth=1, relheight=3/4)

    ttk.Label(
        frame_gauche_haut,
        text="Section gauche haut (3/4)",
        style="TLabel",
        background="#2b2b2b",
        foreground="white"
    ).pack(padx=10, pady=10)

    # == Récapitulatif et paiement - Sous-section gauche bas (1/4) ==
    frame_gauche_bas = ttk.Frame(frame_gauche, style="TFrame", borderwidth=2, relief="solid")
    frame_gauche_bas.place(relx=0, rely=3/4, relwidth=1, relheight=1/4)

    ttk.Label(
        frame_gauche_bas,
        text="Récapitulatif et paiement",
        style="TLabel",
        background="#2b2b2b",
        foreground="white"
    ).pack(padx=10, pady=10)

    # === Section droite (1/3) ===
    frame_droite = ttk.Frame(frame_principal, style="TFrame", borderwidth=2, relief="solid")
    frame_droite.place(relx=2/3, rely=0, relwidth=1/3, relheight=1)

    # == Commandes en cours - Sous-section droite haut (14/15) ==
    frame_droite_haut = ttk.Frame(frame_droite, style="TFrame", borderwidth=2, relief="solid")
    frame_droite_haut.place(relx=0, rely=0, relwidth=1, relheight=14/15)

    ttk.Label(
        frame_droite_haut,
        text="Commandes en cours :\n",
        style="TLabel",
        background="#2b2b2b",
        foreground="white"
    ).pack(padx=10, pady=10)

    # == Sous-section droite bas (1/15) ==
    frame_droite_bas = ttk.Frame(frame_droite, style="TFrame", borderwidth=2, relief="solid")
    frame_droite_bas.place(relx=0, rely=14/15, relwidth=1, relheight=1/15)

    # = Bouton exit =
    frame_exit = ttk.Frame(frame_droite_bas, style="TFrame")
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
