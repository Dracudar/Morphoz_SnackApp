'''
Ce fichier regroupe les fonctions de gestions des fenêtres temporaires (comme les plats ou l'affichage du stock).
Exporte les fonctions de gestion des fenêtres temporaires sous format de bibliothèque.
'''

# === Import === #
from .gestion_temp import travaux_en_cours
from .temp.pizza import pizza_interface_recette
from .temp.grillade import perso_grillade
from .temp.frites import perso_frites
from .temp.salade_composée import perso_salade_composee
from .temp.stock import gestion_stock

# === Export === #
fenetre_plats = {
    "pizza": pizza_interface_recette,
    "grillade": perso_grillade,
    "frites": perso_frites,
    "salade_composée": perso_salade_composee
    }
fenetres_temp = {
    "dev": travaux_en_cours,
    "stock": gestion_stock
    }