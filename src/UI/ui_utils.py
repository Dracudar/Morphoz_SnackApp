import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field

@dataclass
class AppContext:
    root: tk.Tk
    frames: dict = field(default_factory=dict)
    paths: dict = field(default_factory=dict)
    current_view: str = None

def create_main_window():
    root = tk.Tk()  # Création de la fenêtre principale
    root.title("SnackApp Morphoz")  # Titre de la fenêtre
    root.geometry("800x600")  # Définit la taille initiale de la fenêtre
    root.attributes('-fullscreen', True)  # Active le mode plein écran
    root.configure(bg="#2b2b2b")  # Couleur de fond de la fenêtre

    root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))  # Permet de quitter le mode plein écran avec la touche Échap
    root.bind("<F11>", lambda event: root.attributes('-fullscreen', True))  # Permet de basculer en plein écran avec F11
    root.bind("<Control-q>", lambda event: root.destroy())  # Permet de quitter l'application avec Ctrl+Q
    
    return root

def create_frames_structure(context: AppContext, mode="init"):
    # Détruit les frames existants
    for frame in context.frames.values():
        frame.destroy()
    context.frames.clear()
    
    # Crée les frames selon le mode
    if mode == "init":
        frame = ttk.Frame(context.root)
        frame.pack(fill="both", expand=True)
        context.frames["init"] = frame
    elif mode == "main":
        frame = ttk.Frame(context.root)
        frame.pack(fill="both", expand=True)
        context.frames["main"] = frame

def show_view(context: AppContext, view_name: str):
    # Détruit la vue courante
    for widget in context.root.winfo_children():
        widget.destroy()

    # Crée la structure de frames pour la vue demandée
    create_frames_structure(context, mode=view_name)

    # Appelle la fonction de vue correspondante
    if view_name == "init":
        from .views.init_view import render_init_view
        render_init_view(context, context.frames["init"])
        context.current_view = "init"
    elif view_name == "main":
        from .views.main_view import render_main_view
        render_main_view(context, context.frames["main"])
        context.current_view = "main"

def refresh_main_view(context):
    from .views.main_view import render_main_view
    # Détruit et recrée la vue principale (frames, boutons, etc.)
    render_main_view(context, context.frames["main"])

