'''
Point d'entrée de l'application SnackApp
'''

# Importer les modules nécessaires
import tkinter as tk
from tkinter import filedialog, messagebox
import json
from Morphoz_SnackApp.utils import charger_stock

# Variables globales
menu = None
stock = None

def verifier_stock(menu, stock):
    '''Vérifie si les ingrédients du menu sont présents dans le stock.'''
    ingredients_menu = set()
    for categorie, details in menu.items():
        if isinstance(details, dict):
            for sous_categorie, contenu in details.items():
                if isinstance(contenu, list):
                    ingredients_menu.update(contenu)
                elif isinstance(contenu, dict):
                    for _, valeurs in contenu.items():
                        if isinstance(valeurs, list):
                            ingredients_menu.update(valeurs)

    ingredients_stock = set(stock.keys())
    manquants = ingredients_menu - ingredients_stock

    if manquants:
        messagebox.showwarning("Stock incomplet", f"Les ingrédients suivants sont manquants dans le stock : {', '.join(manquants)}")
    else:
        messagebox.showinfo("Stock vérifié", "Tous les ingrédients du menu sont disponibles dans le stock.")

    return manquants

def charger_menu():
    '''Charge le fichier menu sélectionné par l'utilisateur.'''
    global menu, stock

    # Ouvrir une boîte de dialogue pour sélectionner le fichier menu
    fichier_menu = filedialog.askopenfilename(
        title="Sélectionnez le fichier menu",
        filetypes=[("Fichiers JSON", "*.json")]
    )

    if not fichier_menu:
        messagebox.showinfo("Annulation", "Le programme va s'arrêter.")
        root.quit()
        return

    try:
        with open(fichier_menu, "r", encoding="utf-8") as f:
            menu = json.load(f)
        messagebox.showinfo("Menu chargé", f"Le menu '{fichier_menu}' a été chargé avec succès.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de charger le menu : {e}")
        return

    # Charger le stock
    try:
        stock = charger_stock("stock.json")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de charger le stock : {e}")
        return

    # Vérifier le stock par rapport au menu
    manquants = verifier_stock(menu, stock)

    # Afficher le résultat de la corrélation
    if not manquants:
        messagebox.showinfo("Corrélation réussie", "Le menu et le stock sont compatibles.")
    else:
        messagebox.showwarning("Corrélation incomplète", "Certains ingrédients sont manquants. Veuillez vérifier le stock.")

# Initialiser l'interface graphique
if __name__ == "__main__":
    root = tk.Tk()
    root.title("SnackApp - Sélection du menu")
    tk.Button(root, text="Sélectionner un menu", command=charger_menu).pack(pady=20)
    tk.Button(root, text="Annuler", command=root.quit).pack(pady=10)

    # Lancer l'application
    root.mainloop()