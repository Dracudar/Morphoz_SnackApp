'''
Ce fichier regroupe les fonctions de gestions des fenêtres temporaires (comme les plats ou l'affichage du stock).
Exporte les fonctions de gestion des fenêtres temporaires sous format de bibliothèque.
'''

# === Import === #
from src.temp.front_temp import travaux_en_cours
from src.temp.front_temp_pizza import pizza_interface_recette
from src.temp.front_temp_grillade import perso_grillade
from src.temp.front_temp_frites import perso_frites
from src.temp.front_temp_salade_composée import perso_salade_composee

# === Export === #
fenetre_temp = {
    "dev": travaux_en_cours,
    "pizza": pizza_interface_recette,
    "grillade": perso_grillade,
    "frites": perso_frites,
    "salade_composée": perso_salade_composee
}