'''
Code GUI de l'application SnackApp de Morphoz
'''

### Importer les modules nécessaires
# Modules pour l'interface graphique
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from utils import chercher_fichier  # Import de la fonction déplacée

### Interfaces d'initialisation de l'app permettant la vérification des fichier JSON et leur chargement
def menu_initialisation():
    # Création de la fenêtre principale
    root = tk.Tk()
    root.title("Initialisation - SnackApp")
    root.geometry("703x160")
    root.configure(bg="#2b2b2b")  # Couleur de fond sombre

    # Variables pour stocker les chemins des fichiers JSON
    stock_file_path = tk.StringVar()
    menu_file_path = tk.StringVar()

    # Fonction pour vérifier les fichiers et passer au menu principal
    def demarrer_menu_principal():
        if not stock_file_path.get() or not menu_file_path.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner les deux fichiers JSON.")
            return
        # Ici, ajouter une vérification de la validité des fichiers JSON si nécessaire
        messagebox.showinfo("Succès", "Fichiers validés. Chargement du menu principal...")
        root.destroy()
        menu_principal()

    # Fonction pour arrêter l'application
    def quitter_application():
        root.destroy()

    # Interface utilisateur
    ttk.Label(root, text="Stock :", foreground="white", background="#2b2b2b", font=("Cambria", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
    ttk.Entry(root, textvariable=stock_file_path, width=60, font=("Cambria", 10)).grid(row=0, column=1, padx=10, pady=10)
    ttk.Button(root, text="Chercher", command=lambda: stock_file_path.set(chercher_fichier()), style="TButton").grid(row=0, column=2, padx=10, pady=10, sticky="e")

    ttk.Label(root, text="Menu :", foreground="white", background="#2b2b2b", font=("Cambria", 12)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
    ttk.Entry(root, textvariable=menu_file_path, width=60, font=("Cambria", 10)).grid(row=1, column=1, padx=10, pady=10)
    ttk.Button(root, text="Chercher", command=lambda: menu_file_path.set(chercher_fichier()), style="TButton").grid(row=1, column=2, padx=10, pady=10, sticky="e")

    # Boutons en bas
    ttk.Button(root, text="Quitter", command=quitter_application, style="TButton").grid(row=3, column=0, columnspan=1, padx=10, pady=20, sticky="nsew")
    ttk.Button(root, text="Démarrer", command=demarrer_menu_principal, style="TButton").grid(row=3, column=1, columnspan=2, padx=10, pady=20, sticky="nsew")

    # Configuration du style pour appliquer la police Cambria aux boutons
    style = ttk.Style()
    style.configure("TButton", font=("Cambria", 12))

    # Lancer la boucle principale
    root.mainloop()

### Interface principale de l'application
def menu_principal():
    # Exemple de menu principal (à compléter)
    print("Menu principal chargé.")