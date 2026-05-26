# Morphoz_SnackApp

Application de gestion de snack pour événements (ex : MégaSouye), développée pour l'association Morphoz.

## Fonctionnalités principales

- **Prise de commande** (pizzas, grillades, frites, fish & chips, salades composées, etc.)
- **Personnalisation des plats** (choix des ingrédients, accompagnements, etc.)
- **Gestion des stocks** (mise à jour automatique selon les commandes)
- **Suivi des commandes** (statuts : en attente, en préparation, prêt, livré)
- **Gestion des paiements** (CB, espèces, repas gratuits)
- **Impression de tickets** (pour chaque plat et pour la commande globale)
- **Archivage automatique** des commandes terminées

## Installation

1. **Cloner le dépôt**  
   ```bash
   git clone <url_du_repo>
   cd Morphoz_SnackApp
   ```

2. **Installer les dépendances**  
   Python 3.10+ recommandé.  
   ```bash
   pip install -r requirements.txt
   ```
   Les dépendances principales sont :
   - `tkinter`
   - `Pillow`
   - `python-escpos` (pour l'impression de tickets)
   - `pytest` (pour les tests)

3. **Lancer l'application**  
   ```bash
   python -m src.UI.app
   ```

## Structure détaillée du projet

```
Morphoz_SnackApp/
│
├── src/
│   ├── UI/
│   │   ├── app.py                      # Point d'entrée de l'interface graphique
│   │   ├── styles.py                   # Définition des styles graphiques (Tkinter)
│   │   ├── ui_utils                    # Gestion de systèmes d'affichages
│   │   └── views/
│   │       └── init_view.py            # Vue d'initialisation (sélection fichiers, etc.)
│   │       └── main_view.py            # Vue principale (prise et suivi des commandes)
│   │
│   ├── frontend/
│   │   ├── boutons_utilitaires.py      # Boutons utilitaires (retour, exit, gestion stock, etc.)
│   │   ├── commandes_saisie.py         # Affichage et gestion de la commande en cours
│   │   ├── commandes_suivi.py          # Suivi des commandes validées et en préparation
│   │   ├── explorateurs_fichiers.py    # Sélection des fichiers/dossiers via dialogues
│   │   └── temp/
│   │       ├── frites.py               # UI pour ajout de frites à la commande
│   │       ├── fish_and_chips.py       # UI pour ajout de fish & chips
│   │       ├── grillade.py             # UI pour personnalisation des grillades
│   │       ├── salade_composée.py      # UI pour personnalisation des salades composées
│   │       └── stock.py                # UI de gestion des stocks (onglets, quantités, ruptures)
│   │
│   ├── backend/
│   │   ├── chemins_exploitation.py     # Chargement des fichiers JSON, initialisation des dossiers
│   │   ├── chemins_gestion.py          # Gestion et sauvegarde des chemins de fichiers
│   │   ├── commandes_saisie_save.py    # Création/mise à jour des fichiers de commande
│   │   ├── commandes_saisie_gestion.py # Validation, annulation, gestion des statuts de commande
│   │   ├── commandes_suivi_gestion.py  # Changement de statut des plats (prêt, livré, terminé)
│   │   ├── commandes_utils.py          # Utilitaires : génération d'ID, chargement JSON sécurisé
│   │   └── printer.py                  # Impression des tickets (plats et commandes)
│   │
│   └── utils/                          # (optionnel) Fonctions utilitaires partagées
│
├── tests/
│   ├── printer.py                      # Tests d'impression de tickets
│   └── ...                             # Autres tests unitaires
│
├── requirements.txt                    # Dépendances Python du projet
├── README.md                           # Documentation du projet
└── .gitignore                          # Fichiers à ignorer par git
```

## Utilisation

Au lancement, l'application propose de sélectionner les fichiers de stock et de menu, puis permet la prise de commandes, la personnalisation des plats, la validation et le suivi en temps réel.

Les tickets sont imprimés automatiquement à chaque validation de commande.

## Développement

- **Ajouter une fonctionnalité** : Créer un module dans `src/frontend/temp/` ou `src/backend/` selon le besoin.
- **Tests** : Ajouter vos tests dans le dossier `tests/` et lancer avec `pytest`.

## Auteurs

- Projet développé par Dracudar pour l'association Morphoz.

## Licence

Projet open-source sous licence MIT.

---

*Pour toute question ou contribution, contactez l'équipe Morphoz !*