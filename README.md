# Morphoz_SnackApp

Application de gestion de snack pour événements (ex : MégaSouye), développée pour l'association Morphoz.

## Fonctionnalités

- **Prise de commande** — navigation par catégories, personnalisation par type de plat (pizzas, grillades, salades composées, crêpes, frites, etc.)
- **Gestion des stocks** — inventaire hiérarchique avec déduction automatique à la validation et restauration à l'annulation
- **Suivi des commandes** — statuts en temps réel (En attente → En préparation → Prêt → Livré)
- **Poste de préparation** — affichage plein écran pour la cuisine, filtrable par type de plat
- **Gestion des paiements** — CB, espèces, repas gratuits
- **Impression de tickets** — tickets client et cuisine via imprimante thermique USB (ESC-POS), réimpression depuis l'historique
- **Gestion de la carte** — édition des catégories, recettes, prix et états (Disponible / Rupture / Retiré / Archivé)
- **Historique des commandes** — recherche, filtres (statut, date, priorité), tri, réimpression
- **Journal d'événements** — traçabilité complète au format JSON Lines (commandes, stock, paiements, paramètres, erreurs)
- **Affichage extérieur** — fenêtre secondaire pour le suivi des commandes côté client

## Utilisation

Au lancement, l'application charge automatiquement la configuration (dossier de données, imprimante). La vue principale est divisée en deux panneaux : saisie des commandes à gauche et suivi en temps réel à droite.

Pour les paramètres (dossier de données, imprimante, options d'impression), accéder au module Paramètres via la barre de navigation.

## Développement & maintenance

### Installation

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/Dracudar/Morphoz_SnackApp
   cd Morphoz_SnackApp
   ```

2. **Créer et activer un environnement virtuel**

   Python 3.14 ou supérieur recommandé.
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

   | Dépendance | Rôle |
   |------------|------|
   | **PySide6** | Interface graphique Qt6 |
   | **Pillow** | Traitement de l'image d'en-tête des tickets |
   | **pyusb** | Communication USB avec l'imprimante |
   | **python-escpos** | Protocole ESC-POS pour imprimantes thermiques |

4. **Lancer l'application**
   ```bash
   python -m src.core.app
   ```

### Structure du projet

```
Morphoz_SnackApp/
│
├── assets/
│   ├── config.json                         # Configuration (dossier données, imprimante, options impression)
│   ├── icons/                              # Icônes SVG (annuler, filtrer, trier, imprimer, sauvegarder)
│   └── imgs/                               # Images (en-tête ticket)
│
├── src/
│   ├── core/
│   │   └── app.py                          # Point d'entrée, initialisation Qt (thème sombre Fusion)
│   │
│   ├── UI/
│   │   ├── main_window.py                  # Fenêtre principale (menus, raccourcis F11/Ctrl+Q)
│   │   ├── suivi_exterieur_window.py       # Fenêtre d'affichage extérieur client
│   │   ├── module_registry.py              # Registre des modules chargés
│   │   └── view/
│   │       └── interface_principale.py     # Assemblage vue principale (panneau gauche + droite)
│   │
│   ├── backend/
│   │   ├── app_config.py                   # Gestion de la configuration (dossier, imprimante, options)
│   │   ├── commandes_utils.py              # Génération d'ID, réconciliation du stock, chargement JSON
│   │   ├── data_sources.py                 # Chargement/sauvegarde centralisé (carte, stock, commandes)
│   │   ├── logger.py                       # Journal d'événements (JSON Lines, fichier quotidien)
│   │   └── printer.py                      # Impression des tickets (ESC-POS, USB)
│   │
│   └── modules/
│       ├── commandes_saisie/               # Saisie des commandes (UI + backend + dialogue paiement)
│       ├── commandes_suivi/                # Suivi en temps réel des commandes (panneau droit)
│       ├── commandes_poste_preparation/    # Poste de préparation cuisine (plein écran)
│       ├── commandes_historique/           # Historique avec filtres, tri et réimpression
│       ├── carte/                          # Gestion de la carte (catégories, recettes, prix, états)
│       ├── stock/                          # Gestion des stocks (liste hiérarchique + formulaire d'édition)
│       ├── parametres/                     # Paramètres (dossier de données, imprimante, impression)
│       └── plats/                          # Dialogues de personnalisation par type de plat
│           ├── pizza/                      # Sélection de recette + personnalisation base/ingrédients
│           ├── grillade/                   # Choix de viande et accompagnement
│           ├── salade_composee/            # Sélection des ingrédients
│           ├── crepe/                      # Choix du type de crêpe
│           └── frites/                     # Choix de la taille
│
├── archive/
│   ├── libusb-1.0.dll                      # Bibliothèque USB (requis Windows)
│   └── zadig-2.9.exe                       # Installateur de pilote USB pour l'imprimante
│
├── scripts/
│   └── printer_tickets_repas.py            # Utilitaire d'impression des tickets repas
│
├── requirements.txt                        # Fichier des dépendances Python
├── README.md
└── CLAUDE.md
```

## Auteurs

- Dracudar

## Licence

Projet open-source sous licence MIT.

## Historique des versions

<table>
  <tr>
    <th>Version</th>
    <th>Date de sortie</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>1.2.2</td>
    <td>17/06/2025</td>
    <td>Première version de production (Tkinter)</td>
  </tr>
  <tr>
    <td>2.0.0</td>
    <td>—</td>
    <td>Réécriture complète en Qt (PySide6) — version actuelle</td>
  </tr>
</table>

---

*Pour toute question ou contribution, contactez l'équipe Morphoz !*
