'''
Fichier pour regrouper les imports de tous les modules de l'application SnackApp.

'''
# Utilitaires
from src.utils import (
    charger_chemins,
    initialiser_chemins,
    sauvegarder_chemins,
    charger_donnees_stock,
    charger_donnees_menu,
    chercher_fichier,
    chercher_dossier,
    sauvegarder_chemin_stock,
    sauvegarder_chemin_menu,
    sauvegarder_chemin_dossier,
    initialiser_dossier_archive,
    charger_img
)

# Backend
from src.back import (
    ajouter_ou_mettre_a_jour_commande,
    valider_commande,
    plat_prêt,
    livrer_plat,
    terminer_commande,
    annuler_commande,
    annuler_plat,
    modifier_plat,
    charger_fichier_json
)

# Frontend temporaire
from src.front_temp import (
    perso_pizza,
    perso_grillade,
    perso_salade_composee,
    perso_frites,
    gestion_stock,
    travaux_en_cours
)

# Styles
from src.styles import configurer_styles