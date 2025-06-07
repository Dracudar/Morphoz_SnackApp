import tkinter as tk
from tkinter import ttk

root = tk.Tk()
for i in range(100):
    ttk.Label(root, text=f"Ligne {i}").pack()
root.mainloop()