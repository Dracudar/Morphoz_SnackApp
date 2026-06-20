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
- **Application légère pour postes cuisine** — point d'entrée `app_prep.py` sans dépendances USB ni modules de gestion (adapté aux machines à 4 Go RAM, partage réseau LAN)
- **Vérification des mises à jour** — détection automatique en arrière-plan via l'API GitHub Releases

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

   Python 3.12 ou supérieur recommandé.
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
   | **Pillow** | Traitement des images pour l'impression |
   | **pyusb** | Communication USB avec l'imprimante |
   | **python-escpos** | Protocole ESC-POS pour imprimantes thermiques |
   | **svglib** | Conversion SVG → image pour l'impression |
   | **reportlab** | Rendu vectoriel utilisé par svglib |

4. **Lancer l'application**
   ```bash
   # Application principale (caisse + cuisine + gestion)
   python -m src.core.app

   # Application allégée pour postes cuisine (sans impression USB)
   python -m src.core.app_prep
   ```

### Structure du projet

```
Morphoz_SnackApp/
│
├── assets/
│   ├── config.json                         # Configuration (dossier données, imprimante, options impression)
│   ├── icons/                              # Icônes SVG (annuler, filtrer, trier, imprimer, sauvegarder)
│   └── imgs/                               # Images vectorielles (logos SVG)
│       ├── MegaSnack.svg                   # En-tête ticket + barre de navigation
│       ├── logo_snack.svg                  # Icône de l'application
│       └── logo_MegaSouye.svg              # Logo événement
│
├── src/
│   ├── core/
│   │   ├── app.py                          # Point d'entrée principal (thème sombre Fusion, vérif MAJ)
│   │   ├── app_prep.py                     # Point d'entrée allégé pour postes cuisine (sans USB)
│   │   └── version.py                      # Version centralisée (APP_VERSION)
│   │
│   ├── UI/
│   │   ├── main_window.py                  # Fenêtre principale (raccourcis F11/Ctrl+Q, bannière MAJ)
│   │   ├── suivi_exterieur_window.py       # Fenêtre d'affichage extérieur client
│   │   ├── module_registry.py              # Registre des modules chargés
│   │   └── view/
│   │       ├── interface_principale.py     # Assemblage vue principale (panneau gauche + droite)
│   │       └── volet_navigation.py         # Volet de navigation latéral tactile
│   │
│   ├── UI_prep/
│   │   ├── main_window_prep.py             # Fenêtre principale de l'application légère
│   │   └── panneau_lateral.py              # Volet de configuration (dossier data, plein écran)
│   │
│   ├── backend/
│   │   ├── app_config.py                   # Gestion de la configuration (dossier, imprimante, options)
│   │   ├── commandes_utils.py              # Génération d'ID, réconciliation du stock, chargement JSON
│   │   ├── data_sources.py                 # Chargement/sauvegarde centralisé (carte, stock, commandes)
│   │   ├── logger.py                       # Journal d'événements (JSON Lines, fichier quotidien)
│   │   ├── printer.py                      # Impression des tickets (ESC-POS, USB, PNG+SVG)
│   │   └── update_checker.py               # Vérification mises à jour GitHub (QThread)
│   │
│   ├── utils/
│   │   └── tactile.py                      # Composants Qt tactiles (ScrollAreaTactile, BoutonTactile, EnTeteCliquable)
│   │
│   └── modules/
│       ├── commandes_saisie/               # Saisie des commandes (UI + backend + dialogue paiement)
│       ├── commandes_suivi/                # Suivi en temps réel des commandes (panneau droit)
│       ├── commandes_poste_preparation/    # Poste de préparation cuisine (plein écran)
│       ├── commandes_historique/           # Historique avec filtres, tri et réimpression
│       ├── carte/                          # Gestion de la carte (catégories, recettes, prix, états)
│       ├── stock/                          # Gestion des stocks (liste hiérarchique + formulaire d'édition)
│       ├── logs/                           # Consultation du journal d'événements avec filtres et tri
│       ├── parametres/                     # Paramètres (dossier de données, imprimante, impression)
│       └── plats/                          # Dialogues de personnalisation par type de plat
│           ├── pizza/                      # Sélection de recette + personnalisation base/ingrédients
│           ├── grillade/                   # Choix de viande et accompagnement
│           ├── salade_composee/            # Sélection des ingrédients
│           ├── crepe/                      # Choix du type de crêpe
│           └── frites/                     # Choix de la taille
│
├── .github/
│   └── workflows/
│       ├── auto-tag.yml                    # Vérifie la doc, génère le CHANGELOG, crée le tag vX.Y.Z et déclenche build.yml
│       └── build.yml                       # CI/CD : 6 builds PyInstaller (Windows + Linux x86_64/aarch64 × main/prep), appelé par auto-tag.yml
│
├── morphoz_snackapp.spec                   # Configuration PyInstaller (application principale)
├── morphoz_prep.spec                       # Configuration PyInstaller (application légère)
│
├── archive/
│   ├── libusb-1.0.dll                      # Bibliothèque USB (requis Windows)
│   └── zadig-2.9.exe                       # Installateur de pilote USB pour l'imprimante
│
├── scripts/
│   ├── generate_changelog.py               # Génère l'entrée CHANGELOG.md d'une version (utilisé par auto-tag.yml)
│   └── printer_tickets_repas.py            # Utilitaire d'impression des tickets pour repas gratuits
│
├── docs/
│   ├── ARCHITECTURE.md                     # Documentation d'architecture détaillée
│   └── PATCHNOTE_VX.Y.0.md                  # Patch note utilisateur par version majeure/mineure
│
├── requirements.txt                        # Fichier des dépendances Python
├── CHANGELOG.md                            # Historique détaillé généré automatiquement à chaque version
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
    <td>11/06/2026</td>
    <td>Réécriture complète en Qt (PySide6)</td>
  </tr>
  <tr>
    <td>2.1.0</td>
    <td>16/06/2026</td>
    <td>Navigation tactile (volet latéral), logos SVG, application légère postes cuisine, compilation PyInstaller multi-plateforme, vérificateur de mises à jour</td>
  </tr>
  <tr>
    <td>2.1.1</td>
    <td>18/06/2026</td>
    <td>Correction du pipeline CI/CD : le tag et la compilation/release s'enchaînent désormais dans le même run GitHub Actions</td>
  </tr>
  <tr>
    <td>2.1.2</td>
    <td><em>18/06/2026</em></td>
    <td>Correction de bugs de compilation PyInstaller : capabilities.json d'escpos non inclus, dossier data non créé au premier lancement, chemins d'assets relatifs invalides dans le dossier _internal</td>
  </tr>
  <tr>
    <td>2.2.0</td>
    <td><em>20/06/2026</em></td>
    <td>Sécurisation des accès concurrents aux fichiers JSON partagés en LAN (verrouillage inter-processus, écriture atomique), correction d'un bug d'affichage du volet de navigation, vérification automatique de la documentation et CHANGELOG généré automatiquement avant chaque release</td>
  </tr>
  <tr>
    <td>2.2.1</td>
    <td><em>20/06/2026</em></td>
    <td>Ajout de la compilation Linux <code>aarch64</code> (Raspberry Pi 5) dans le pipeline CI, en complément de <code>x86_64</code></td>
  </tr>
</table>

---

*Pour toute question ou contribution, contactez l'équipe Morphoz !*
