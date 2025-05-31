"""
Module de gestion des boutons de prise de commande selon le menu.
"""
from tkinter import ttk, messagebox
from ..backend.chemins_exploitation import (
    charger_donnees_menu,
    charger_donnees_stock
    )
from ..backend.img_import import charger_img
from ..UI.styles import configurer_styles
from .export_temp import (
    fenetre_plats,
    fenetres_temp
    )

configurer_styles()

# == Prise de commande : Génération des boutons du menu == #
# Titre de la frame
def affichage_menu(frame_gauche_haut, context, images_references):
    # Titre de la section Menu
    ttk.Label(
        frame_gauche_haut,
        text="Menu",
        style="TLabel",
        background="#2b2b2b",
        foreground="white",
        font=("Cambria", 14, "bold")
    ).pack(padx=10, pady=10)

    menu_path = context.paths.get("menu") if hasattr(context, "paths") else None
    if not menu_path:
        messagebox.showerror("Erreur", "Aucun fichier menu sélectionné.")
        return

    # Charger les données du fichier JSON de menu
    try:
        menu_data = charger_donnees_menu(menu_path)
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
            action = lambda root=context.root: fenetre_plats["pizza"](root)
        elif plat.lower() == "grillade":
            action = lambda root=context.root: fenetre_plats["grillade"](root)
        elif plat.lower() == "salade composée":
            action = lambda root=context.root: fenetre_plats["salade_composée"](root)
        elif plat.lower() == "frites":
            action = lambda root=context.root: fenetre_plats["frites"](root)
        else:
            action = lambda root=context.root: fenetres_temp["dev"](root)
        
        # Créer le bouton avec la fonction dédiée
        structure_boutons_menu(
            parent=frame_boutons,
            plat=plat,
            logo_tk=logo_tk,
            action=action
        )
