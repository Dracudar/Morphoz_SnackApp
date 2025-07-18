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

# Importation des modules de personnalisation des plats
from ..plats.pizza.pizza import pizza_interface_recette
from ..plats.grillade.grillade import perso_grillade
from .temp.fish_and_chips import add_fish_and_chips
from ..plats.frites.frites import add_frites
from ..plats.salade_composée.salade_composée import perso_salade_composee
from ..plats.pizza.pizza_dessert import add_dessert

fenetre_plats = {
    "Pizza": pizza_interface_recette,
    "Grillade": perso_grillade,
    "Fish & Chips": add_fish_and_chips,
    "Frites": add_frites,
    "Salade composée": perso_salade_composee,
    "Pizza dessert": add_dessert
    }

from .temp_gestion import travaux_en_cours as messages_dev

configurer_styles()

# == Prise de commande : Génération des boutons du menu == #
# Titre de la frame
def affichage_menu(context, images_references):
    # Nettoyer la frame avant de réafficher les boutons
    for widget in context.frames_main["gauche_haut"].winfo_children():
        widget.destroy()

    # Titre de la section Menu
    ttk.Label(
        context.frames_main["gauche_haut"],
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
        menu_data = charger_donnees_menu(context.paths)
        stock_data = charger_donnees_stock(context.paths)
    except (FileNotFoundError, ValueError) as e:
        messagebox.showerror("Erreur", str(e)) 
        return

    # Créer un cadre pour centrer les boutons horizontalement
    frame_boutons = ttk.Frame(context.frames_main["gauche_haut"], style="TFrame")
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

        # === Blocage selon le stock ===
        state = "normal"
        style = "TButton"
        # 1. Pizza & Pizza dessert
        if plat in ("Pizza", "Pizza dessert"):
            if hasattr(context, "stock_cache") and context.stock_cache.is_out_of_stock(["Plats", "Pizza", "Pâte à pizza"]):
                state = "disabled"
                style = "Disabled.TButton"
        # 2. Grillade : désactiver si toutes les viandes sont hors stock
        elif plat == "Grillade":
            if hasattr(context, "stock_cache"):
                viandes = context.stock_cache._stock_cache["Plats"]["Grillades"]
                if all(v.get("OutOfStock", False) for v in viandes.values()):
                    state = "disabled"
                    style = "Disabled.TButton"
        # 3. Frites
        elif plat == "Frites":
            if hasattr(context, "stock_cache") and context.stock_cache.is_out_of_stock(["Accompagnement", "Frites"]):
                state = "disabled"
                style = "Disabled.TButton"
        # 4. Salade composée
        elif plat == "Salade composée":
            if hasattr(context, "stock_cache") and context.stock_cache.is_out_of_stock(["Plats", "Salade composée"]):
                state = "disabled"
                style = "Disabled.TButton"

        # Ajouter le bouton dans le conteneur
        bouton = ttk.Button(
            cadre_bouton,
            text=plat,
            image=logo_tk,
            command=action,  # Appeler l'action associée au bouton
            compound="top",  # Affiche le texte en dessous de l'image
            style=style,
            state=state
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

        # Appel direct par correspondance de clé
        if plat in fenetre_plats:
            action = lambda p=plat: fenetre_plats[p](context)
        else:
            action = lambda: messages_dev(context.root)

        # Créer le bouton avec la fonction dédiée
        structure_boutons_menu(
            parent=frame_boutons,
            plat=plat,
            logo_tk=logo_tk,
            action=action
        )
