'''
Fichier contenant les styles pour le front de l'application SnackApp
'''

from tkinter import ttk

def configurer_styles():
    """Configure les styles pour l'application."""
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