'''
Porte d'entrée de l'application SnackApp Morphoz
'''

from .UI.ui_utils import AppContext, create_main_window, show_view

def main():
    root = create_main_window()
    context = AppContext(root=root)
    show_view(context, "init")
    root.mainloop()

if __name__ == "__main__":
    main()