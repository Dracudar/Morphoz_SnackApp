'''
Code GUI de l'application SnackApp de Morphoz
'''

#! Importer les modules nécessaires
#!! Modules pour l'interface graphique
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
root = tk.Tk()

#!! Import de fonctions externes
from utils import chercher_fichier, sauvegarder_chemins, initialiser_chemins, get_stock_file_path, get_menu_file_path

# Initialiser les chemins
initialiser_chemins()

#!! Arrêt de l'application
def quitter_application():
    sauvegarder_chemins(get_stock_file_path().get(), get_menu_file_path().get())  # Sauvegarder les chemins avant de quitter
    root.destroy()  # Fermer la fenêtre

#!! Configuration du style pour appliquer la police Cambria aux boutons
style = ttk.Style()
style.configure("TButton", font=("Cambria", 12)) # Appliquer la police Cambria aux boutons
style.configure("TLabel", font=("Cambria", 12)) # Appliquer la police Cambria aux labels

#! Interfaces d'initialisation de l'app permettant la vérification des fichier JSON et leur chargement
def menu_initialisation():
    ''' Affichage permettant de choisir les fichiers JSON de stock et de menu '''
    #!! Création de la fenêtre principale
    root.title("SnackApp - Menu d'initialisation")
    root.attributes('-fullscreen', True)  # Active le mode plein écran
    root.configure(bg="#2b2b2b")  # Couleur de fond sombre
    root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))

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

    #!!! Bloc d'instructions 
    # note: modifier pour utiliser des packs
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

### Interface principale de l'application
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

    # Section principale avec pack
    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Widgets dans la section avec place
    ttk.Label(frame, text="Bienvenue", font=("Cambria", 16)).place(relx=0.5, rely=0.1, anchor="center")
    ttk.Button(
        frame,
        text="Quitter",
        command=quitter_application,
        style="TButton"
    ).place(relx=0.5, rely=0.5, anchor="center")
