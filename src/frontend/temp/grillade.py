'''
Code UI pour les interfaces temporaire de personnalisation des grillades
'''

# === Importer les modules nécessaires === #
import os  # Pour manipuler les chemins de fichiers
import tkinter as tk
from tkinter import ttk, messagebox

from src.backend.commandes_saisie_save import MAJ_commande
from src.frontend.temp_gestion import ouvrir_fenetre_unique 
from ...backend.chemins_exploitation import (
    charger_donnees_menu, 
    charger_donnees_stock,
    )

# === Définitions des fonctions === #
def perso_grillade(context):
    def creation_fenetre():
        # Charger les données du stock via context
        stock_data = charger_donnees_stock(context.paths)
        viandes_disponibles = stock_data.get("Plats", {}).get("Grillades", {})
        accompagnements_disponibles = stock_data.get("Accompagnement", {})
        accompagnements_disponibles = ["Sans"] + [acc for acc, data in accompagnements_disponibles.items() if not data.get("OutOfStock", False)]

        # Crée une fenêtre pour la personnalisation
        fenetre_grillade = tk.Toplevel(context.root)
        fenetre_grillade.title("Grillade")
        fenetre_grillade.configure(bg="#2b2b2b")
        fenetre_grillade.attributes("-topmost", True)  # Garde la fenêtre au premier plan

        # Variables pour suivre les quantités de viandes
        quantites_viandes = {viande: tk.IntVar(value=0) for viande in viandes_disponibles}

        # Variable pour l'accompagnement sélectionné
        accompagnement_selectionne = tk.StringVar(value="Frites")

        # Fonction pour ajuster les quantités
        def ajuster_quantite(viande, delta):
            """
            Ajuste la quantité de viande sélectionnée en respectant la limite totale de 2 portions
            et empêche les valeurs négatives.
            """
            # Récupère la valeur de la viande depuis le dictionnaire
            valeur_viande = viandes_disponibles.get(viande, {}).get("Valeur", 0)
            
            # Calcule le total actuel en fonction des quantités et des valeurs des viandes
            total_actuel = sum(
                quantites_viandes[v].get() * viandes_disponibles.get(v, {}).get("Valeur", 0)
                for v in quantites_viandes
            )

            # Calcule la nouvelle valeur
            nouvelle_valeur = quantites_viandes[viande].get() + delta

            # Vérifie que la nouvelle valeur est positive et que le total ne dépasse pas 2 portions
            if 0 <= nouvelle_valeur <= 2 and 0 <= nouvelle_valeur * valeur_viande + total_actuel - quantites_viandes[viande].get() * valeur_viande <= 2:
                quantites_viandes[viande].set(nouvelle_valeur)

        # Affichage des viandes
        ttk.Label(
            fenetre_grillade,
            text="Choisissez vos viandes (max 2 portions) :",
            font=("Cambria", 14),
            background="#2b2b2b",
            foreground="white"
        ).pack(pady=10)

        for viande in viandes_disponibles:
            frame_viande = ttk.Frame(fenetre_grillade)
            frame_viande.pack(fill="x", padx=20, pady=5)

            ttk.Label(
                frame_viande,
                text=viande,
                font=("Cambria", 12),
                width=20
            ).pack(side="left")

            ttk.Button(
                frame_viande,
                text="-",
                command=lambda v=viande: ajuster_quantite(v, -1)
            ).pack(side="left", padx=5)

            ttk.Label(
                frame_viande,
                textvariable=quantites_viandes[viande],
                width=5,
                anchor="center"
            ).pack(side="left")

            ttk.Button(
                frame_viande,
                text="+",
                command=lambda v=viande: ajuster_quantite(v, 1)
            ).pack(side="left", padx=5)

        # Affichage des accompagnements
        ttk.Label(
            fenetre_grillade,
            text="Choisissez un accompagnement :",
            font=("Cambria", 14),
            background="#2b2b2b",
            foreground="white"
        ).pack(pady=10)

        frame_accompagnements = ttk.Frame(fenetre_grillade)
        frame_accompagnements.pack(pady=10)

        for i, accompagnement in enumerate(accompagnements_disponibles):
            ttk.Radiobutton(
                frame_accompagnements,
                text=accompagnement,
                variable=accompagnement_selectionne,
                value=accompagnement,
                style="TRadiobutton",
                width=15  # Uniformiser la largeur
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")  # Positionner côte à côte

        # Bouton pour valider la personnalisation
        def valider_grillade():
            """
            Valide la personnalisation de la grillade et ajoute la commande au fichier.
            """
            # Récupérer les viandes choisies et leurs quantités
            viandes_choisies = {viande: quantites_viandes[viande].get() for viande in viandes_disponibles if quantites_viandes[viande].get() > 0}
            accompagnement = accompagnement_selectionne.get()

            if not viandes_choisies:
                messagebox.showerror("Erreur", "Veuillez sélectionner au moins une viande.")
                return

            # Construire le message pour la commande
            if accompagnement == "Sans":
                message = f"Grillade : {' et '.join([f'{q} {v}' for v, q in viandes_choisies.items()])} sans accompagnement"
            else:
                message = f"Grillade : {' et '.join([f'{q} {v}' for v, q in viandes_choisies.items()])} avec {accompagnement}"

            # Charger le prix des grillades depuis le fichier menu via context
            menu_data = charger_donnees_menu(context.paths)
            prix_grillade = menu_data.get("Grillade", {}).get("Prix", 0)

            # Préparer les données du plat
            plat = {
                "Plat": "Grillade",
                "Nom": message,
                "Statut": "En attente",
                "Prix": prix_grillade,
                "Composition": {
                    "Viandes": viandes_choisies,
                    "Accompagnement": accompagnement
                }
            }

            # Utiliser les chemins d'archive depuis context
            commandes_path = os.path.join(context.paths["archive"], "commandes")
            logs_path = os.path.join(context.paths["archive"], "logs")

            # Ajouter ou mettre à jour la commande
            MAJ_commande(commandes_path, logs_path, plat)

            # Rafraîchir l'affichage de la commande actuelle
            from ...frontend.commandes_saisie import affichage_commande_actuelle
            affichage_commande_actuelle(context)

            # Fermer la fenêtre
            fenetre_grillade.destroy()

        ttk.Button(
            fenetre_grillade,
            text="Valider",
            command=valider_grillade
        ).pack(pady=20)

        # Ajuster automatiquement la taille de la fenêtre
        fenetre_grillade.update_idletasks()
        fenetre_grillade.geometry("")

        # Retourner la fenêtre créée
        return fenetre_grillade

    # Utiliser la fonction pour ouvrir une fenêtre unique
    ouvrir_fenetre_unique("Grillade", creation_fenetre, fermer_autres=True)
