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
    #!! Création de la fenêtre principale
    root.title("SnackApp - Menu d'initialisation")
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
    # Réutiliser l'instance existante de root
    root.title("SnackApp - Menu principal")
    root.attributes('-fullscreen', True)  # Active le mode plein écran
    root.configure(bg="#2b2b2b")  # Couleur de fond sombre
    root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))
    root.bind("<F11>", lambda event: root.attributes('-fullscreen', True))


    # Cadre principal
    frame_principal = ttk.Frame(root, style="TFrame")
    frame_principal.pack(fill="both", expand=True, padx=20, pady=20)

    # Section des catégories (haut gauche)
    frame_categories = ttk.Frame(frame_principal, style="TFrame")
    frame_categories.place(relx=0.05, rely=0.05, relwidth=0.6, relheight=0.6)

    categories = ["Pizza", "Grillade", "Frite", "Salade composée"]
    for i, categorie in enumerate(categories):
        ttk.Button(
            frame_categories,
            text=categorie,
            style="TButton"
        ).grid(row=0, column=i, padx=10, pady=10)

    # Section des commandes en cours (haut droite)
    frame_commandes = ttk.Frame(frame_principal, style="TFrame")
    frame_commandes.place(relx=0.7, rely=0.05, relwidth=0.25, relheight=0.6)

    ttk.Label(
        frame_commandes,
        text="Commandes en cours :",
        style="TLabel"
    ).pack(anchor="nw", padx=10, pady=10)

    # Section récapitulatif (bas gauche)
    frame_recap = ttk.Frame(frame_principal, style="TFrame")
    frame_recap.place(relx=0.05, rely=0.7, relwidth=0.6, relheight=0.2)

    ttk.Label(
        frame_recap,
        text="Récap de la prise de commande {aaaammjj-000} :",
        style="TLabel"
    ).pack(anchor="nw", padx=10, pady=10)

    # Section montant et paiement (bas droite)
    frame_paiement = ttk.Frame(frame_principal, style="TFrame")
    frame_paiement.place(relx=0.7, rely=0.7, relwidth=0.25, relheight=0.2)

    ttk.Label(
        frame_paiement,
        text="Montant : 0,00 €",
        style="TLabel"
    ).pack(anchor="nw", padx=10, pady=10)

    boutons_paiement = ["CB", "Espèce", "Gratuit"]
    for i, bouton in enumerate(boutons_paiement):
        ttk.Button(
            frame_paiement,
            text=bouton,
            style="TButton"
        ).pack(side="top", fill="x", padx=10, pady=5)

    # Bouton quitter (en bas à droite)
    ttk.Button(
        frame_principal,
        text="Quitter",
        command=quitter_application,
        style="TButton"
    ).place(relx=0.9, rely=0.9, anchor="center")

    # Bouton paramètres (en bas à gauche)
    logo_parametres_tk = charger_logo("Logos/roue_dentee.png", taille=(30, 30))  # Charger le logo des paramètres
    bouton_parametres = ttk.Button(
        frame_principal,
        image=logo_parametres_tk,
        command=lambda: print("Paramètres"),
        style="TButton"
    )
    bouton_parametres.image = logo_parametres_tk  # Préserver la référence pour éviter le garbage collection
    bouton_parametres.place(relx=0.05, rely=0.9, anchor="w")



    # Exemple pour un autre logo (par exemple, un logo d'aide)
    logo_aide_tk = charger_logo("Logos/aide.png", taille=(30, 30))  # Charger le logo d'aide
    bouton_aide = ttk.Button(
        frame_principal,
        image=logo_aide_tk,
        command=lambda: print("Aide"),
        style="TButton"
    )
    bouton_aide.image = logo_aide_tk  # Préserver la référence pour éviter le garbage collection
    bouton_aide.place(relx=0.1, rely=0.9, anchor="w")