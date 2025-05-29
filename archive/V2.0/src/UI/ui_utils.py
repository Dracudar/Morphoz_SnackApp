import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass, field

@dataclass
class AppContext:
    root: tk.Tk
    frames: dict = field(default_factory=dict)
    paths: dict = field(default_factory=dict)

def create_main_window():
    root = tk.Tk()
    root.title("SnackApp Morphoz")
    root.geometry("800x600")
    root.configure(bg="#2b2b2b")
    # Ajoute ici les raccourcis clavier si besoin
    root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))
    root.bind("<F11>", lambda event: root.attributes('-fullscreen', True))
    root.bind("<Control-q>", lambda event: quitter_app(root))
    return root

def quitter_app(root):
    root.destroy()

def create_frames_structure(context: AppContext, mode="init"):
    # Crée les frames selon le mode (init ou main)
    # Remplit context.frames avec les frames créés
    pass

def show_view(context: AppContext, view_name: str):
    # Détruit les widgets de la vue courante et affiche la nouvelle vue
    pass