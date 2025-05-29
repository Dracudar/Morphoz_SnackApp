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

    # Configuration du style pour les boutons de selection unique (TRadiobutton)
    style.configure(
        "TRadiobutton", 
        font=("Cambria", 12),  # Définit la police et sa taille
        relief="flat",  # Style de bouton plat pour un design moderne
        background="#444444",  # Couleur de fond sombre
        foreground="white"  # Texte en blanc pour un bon contraste
    )
    style.map(
        "TRadiobutton", 
        background=[("active", "#555555")]  # Changer la couleur de fond lorsque le bouton est actif (interactif)
    )

    # Configuration du style pour les boutons de selection multiples (TCheckbutton)
    style.configure(
        "TCheckbutton",
        font=("Cambria", 12),  # Définit la police et sa taille
        relief="flat",  # Style de bouton plat pour un design moderne
        background="#444444",  # Couleur de fond sombre
        foreground="white"  # Texte en blanc pour un bon contraste
    )
    style.map(
        "TCheckbutton",
        background=[("active", "#555555")]  # Changer la couleur de fond lorsque le bouton est actif (interactif)
    )

    # Configuration du style pour les listes déroulantes (TCombobox)
    style.configure(
        "TCombobox",
        font=("Cambria", 12),  # Définit la police et sa taille
        fieldbackground="#444444",  # Couleur de fond sombre pour le champ
        background="#2b2b2b",  # Couleur de fond sombre pour la liste déroulante
        foreground="white"  # Texte en blanc pour un bon contraste
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", "#444444")],  # Couleur de fond pour les champs en lecture seule
        foreground=[("readonly", "white")],  # Texte en blanc pour les champs en lecture seule
        background=[("active", "#555555")]  # Couleur de fond lorsque la liste est active
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
        font=("Cambria", 12),  # Définit la police et sa taille
        fieldbackground="#444444",  # Couleur de fond sombre
        foreground="white"  # Texte en blanc pour un bon contraste
    )

    # Configuration du style pour les cadres / conteneurs principaux (TFrame)
    style.configure(
        "TFrame", 
        background="#2b2b2b"  # Couleur de fond sombre
    )