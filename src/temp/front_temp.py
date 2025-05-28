'''
Code UI pour la gestion des fenêtres d'interfaces temporaire de l'application SnackApp.
Définition d'un message d'information pour indiquer que la fonctionnalité est en cours de développement.
'''

# === Importer les modules nécessaires === #
from UI.front import * # Modules Tinker

# === Suivi des fenêtres ouvertes === #
fenetres_ouvertes: dict[str, tk.Toplevel] = {}

def ouvrir_fenetre_unique(titre, creation_fenetre, fermer_autres=False):
    """
    Vérifie si une fenêtre avec le même titre est déjà ouverte.
    Si oui, ramène cette fenêtre au premier plan.
    Sinon, crée une nouvelle fenêtre.
    Si `fermer_autres` est True, ferme les autres fenêtres avant d'ouvrir la nouvelle.
    """
    if fermer_autres:
        # Fermer toutes les fenêtres ouvertes
        for fenetre in list(fenetres_ouvertes.values()):
            if fenetre.winfo_exists():
                fenetre.destroy()
        fenetres_ouvertes.clear()

    if titre in fenetres_ouvertes and fenetres_ouvertes[titre].winfo_exists():
        # Ramène la fenêtre existante au premier plan
        fenetres_ouvertes[titre].lift()
        fenetres_ouvertes[titre].focus_force()
    else:
        # Crée une nouvelle fenêtre et l'ajoute au dictionnaire
        fenetre = creation_fenetre()
        fenetres_ouvertes[titre] = fenetre

# === Interface "travaux en cours" === #
def travaux_en_cours(root):
    """
    Fenêtre pour indiquer que la fonctionnalité est en cours de développement.
    """
    messagebox.showinfo(
        "Travaux en cours",
        "Cette fonctionnalité est en cours de développement."
    )

# === Export === #
__all__ = [ouvrir_fenetre_unique, travaux_en_cours]