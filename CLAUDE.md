# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Présentation du projet

Application de gestion de snack pour événements, développée pour l'association Morphoz. Application de bureau PySide6 (Qt6) sans base de données ni API REST — tout repose sur des fichiers JSON locaux. La v2.0.0 est une réécriture complète de la v1 (Tkinter).

## Conventions de code

Toute la documentation, les commentaires, les noms de variables, de fonctions et de classes sont rédigés **en français**.

## Commandes de développement

```bash
# Installation
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .\.venv\Scripts\activate       # Windows
pip install -r requirements.txt

# Lancer l'application
python -m src.core.app

# Tests (aucun test n'existe pour l'instant, mais pytest est configuré)
pytest .
pytest chemin/vers/test_fichier.py::nom_du_test   # test unique
```

Pas de configuration ruff/pyproject.toml dans le dépôt — le linter est présent (`.ruff_cache/` ignoré par git) mais non configuré explicitement.

## Architecture

### Vue d'ensemble

```
MainWindow (QMainWindow)
└── InterfacePrincipaleWidget
    ├── Panneau gauche : QStackedWidget (un widget par module)
    │   ├── SaisieCommandeModule      — prise de commande
    │   ├── StockModule               — inventaire
    │   ├── CarteModule               — éditeur de carte
    │   ├── CommandesHistoriqueModule — historique + réimpression
    │   ├── LogsModule                — consultation du journal
    │   ├── ParametresModule          — config dossier/imprimante
    │   └── PostePreparationModule    — affichage plein écran cuisine
    └── Panneau droit : SuiviCommandesModule (suivi en temps réel, visible en mode saisie)

SuiviExterieurWindow (QDialog)  — fenêtre secondaire affichage client
    └── Activée via le menu "Affichage > Affichage extérieur"
```

### Backend central (`src/backend/`)

| Fichier | Rôle |
|---|---|
| `app_config.py` | Lecture/écriture de `assets/config.json` ; point d'accès unique à la config (dossier de données, imprimante, options d'impression) ; détecte les exécutables PyInstaller (`sys.frozen`) |
| `data_sources.py` | Toutes les opérations I/O JSON : carte, stock, commandes (brouillons, en cours, terminées, annulées) |
| `commandes_utils.py` | Génération d'ID de commande (`YYYYMMDD-###`) et de plat (préfixe type + `###`), cache quotidien `derniers_ID.json`, réconciliation du stock au démarrage |
| `logger.py` | Journal d'événements au format JSON Lines (`data/logs/app_YYYYMMDD.log`) avec index séquentiel |
| `printer.py` | Impression de tickets thermiques USB (ESC-POS) ; nécessite libusb (voir `archive/` pour Windows) |

### Flux de données

1. Au démarrage : `app_config.py` charge `assets/config.json` → `commandes_utils.py` réconcilie le stock depuis les brouillons en suspens.
2. Chaque module accède aux données via `data_sources.py` (pas d'accès fichier direct dans les modules).
3. Les changements inter-modules passent par des signaux PySide6 (`Signal()`), notamment `command_changed` et `config_changed`.
4. Les commandes transitent par des états : brouillon (racine de `commandes/`) → `en_cours/` → `terminee/` ou `annulee/`.

### Modules (`src/modules/`)

Chaque module suit le même schéma :
- Un widget QWidget/QFrame principal exposant `refresh()` ou `reload_from_disk()`.
- Un sous-dossier `UI/` pour les composants visuels et, si nécessaire, un sous-dossier `backend/` pour la logique métier.
- `module_registry.py` découvre dynamiquement les modules via un fichier `module.py` optionnel dans chaque dossier.

### Personnalisation des plats (`src/modules/plats/`)

`plats_router.py` est le point d'entrée central : il reçoit une sélection de plat et dispatche vers le module type correspondant (`pizza/`, `grillade/`, `salade_composee/`, `crepe/`, `frites/`). Chaque type expose un `rooting.py` qui ouvre la boîte de dialogue de personnalisation appropriée.

### Persistance et cache

- **Stock** : cache en mémoire (`StockCache`) avec flag "modifié" ; persisté explicitement à la validation de commande ou à la sauvegarde manuelle.
- **IDs** : `DerniersIDCache` maintient les compteurs quotidiens en mémoire, sauvegardés dans `data/logs/derniers_ID.json`.
- **Config** : toujours relue depuis `assets/config.json` via `app_config.py`, jamais mise en cache dans les modules.

### Structure du dossier de données (configurable)

```
data/
├── stock.json
├── carte_active.json
├── carte_archive.json
├── commandes/
│   ├── commande_*.json   # brouillons
│   ├── en_cours/
│   ├── terminee/
│   ├── annulee/
│   └── corrompu/
└── logs/
    ├── app_YYYYMMDD.log   # JSON Lines
    └── derniers_ID.json
```

Le chemin de ce dossier est défini dans `assets/config.json` (`data_folder`) et peut être modifié dans le module Paramètres. Par défaut : `./data/` à la racine du projet.
