# Morphoz SnackApp — Documentation d'architecture

> Version du document : 1.1 — 25/06/2026 (vérifié à jour pour `APP_VERSION = "2.4.0"`)
> Branche de référence : `develop` (équivalent `main` au moment de la rédaction)

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Stack technique](#2-stack-technique)
3. [Architecture en couches](#3-architecture-en-couches)
4. [Structure des fichiers de données](#4-structure-des-fichiers-de-données)
5. [Couche `core`](#5-couche-core)
6. [Couche `UI`](#6-couche-ui)
7. [Couche `backend`](#7-couche-backend)
   - 7.bis [`src/utils/`](#7bis-srcutils)
8. [Modules métier](#8-modules-métier)
   - 8.1 [commandes\_saisie](#81-commandes_saisie)
   - 8.2 [commandes\_suivi](#82-commandes_suivi)
   - 8.3 [commandes\_historique](#83-commandes_historique)
   - 8.4 [commandes\_poste\_preparation](#84-commandes_poste_preparation)
   - 8.5 [plats](#85-plats)
   - 8.6 [stock](#86-stock)
   - 8.7 [carte](#87-carte)
   - 8.8 [parametres](#88-parametres)
   - 8.9 [logs](#89-logs)
9. [Cycle de vie d'une commande](#9-cycle-de-vie-dune-commande)
10. [Système d'identifiants](#10-système-didentifiants)
11. [Gestion du stock — logique cache](#11-gestion-du-stock--logique-cache)
12. [Système de journalisation](#12-système-de-journalisation)
13. [Impression thermique (ESC-POS)](#13-impression-thermique-esc-pos)
14. [Assets et ressources](#14-assets-et-ressources)
15. [Scripts utilitaires](#15-scripts-utilitaires)
16. [Diagramme de dépendances simplifié](#16-diagramme-de-dépendances-simplifié)

---

## 1. Vue d'ensemble

**Morphoz SnackApp** est une application bureau de gestion de snack pour événements (ex. MégaSouye), développée par l'association Morphoz. Elle a été entièrement réécrite en Qt/PySide6 pour la version 2.0 (juin 2026), en remplaçant l'ancienne version Tkinter (v1.2.2).

L'application couvre l'intégralité du cycle de vente :

| Fonction | Module |
|---|---|
| Prise de commande avec personnalisation par type de plat | `commandes_saisie` + `plats/*` |
| Suivi en temps réel (statuts par plat) | `commandes_suivi` |
| Affichage extérieur public (fenêtre secondaire) | `SuiviExterieurWindow` |
| Poste cuisine plein écran | `commandes_poste_preparation` |
| Historique consultable, filtrable et réimprimable | `commandes_historique` |
| Gestion des stocks avec cache mémoire | `stock` |
| Gestion de la carte (catégories, recettes, prix) | `carte` |
| Impression thermique USB (ESC-POS) | `backend/printer.py` |
| Journalisation exhaustive (JSON Lines) | `backend/logger.py` |
| Configuration (dossier data, imprimante) | `parametres` |
| Accès concurrent aux fichiers JSON partagés en LAN | `backend/file_io.py` |

---

## 2. Stack technique

| Composant | Technologie | Rôle |
|---|---|---|
| Interface graphique | **PySide6** (Qt 6) | Tous les widgets, layouts, signaux/slots, timers |
| Thème | Fusion (dark palette) | Palette sombre personnalisée définie dans `app.py` |
| Persistance | **Fichiers JSON** | Commandes, stock, carte, config, IDs cache |
| Journalisation | **JSON Lines** | Un fichier `.log` par jour dans `data/logs/` |
| Impression | **python-escpos** + **pyusb** | Tickets thermiques USB (protocole ESC-POS) |
| Images tickets | **Pillow** + **svglib** + **reportlab** | Chargement PNG, conversion SVG→PNG pour l'imprimante |
| Python | ≥ 3.14 | Typage, f-strings, pathlib, importlib |

**Dépendances** (`requirements.txt`) :
```
PySide6
pillow
pyusb
python-escpos
svglib
reportlab
filelock
```

---

## 3. Architecture en couches

```
┌──────────────────────────────────────────────────────────────────┐
│                        POINTS D'ENTRÉE                           │
│   src/core/app.py (application principale)                       │
│   src/core/app_prep.py (application légère postes cuisine)       │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│                      COUCHE UI                                   │
│  main_window.py ─ InterfacePrincipaleWidget ─ module_registry    │
│  volet_navigation.py ─ SuiviExterieurWindow                      │
│  UI_prep/ : main_window_prep.py ─ panneau_lateral.py             │
└────────────┬──────────────────────────────────────┬─────────────┘
             │                                      │
┌────────────▼──────────────────┐  ┌───────────────▼────────────┐
│   MODULES UI (src/modules/)   │  │   COUCHE BACKEND           │
│   commandes_saisie            │  │   app_config.py            │
│   commandes_suivi             │◄─┤   data_sources.py          │
│   commandes_historique        │  │   commandes_utils.py       │
│   commandes_poste_preparation │  │   logger.py                │
│   carte / stock / logs        │  │   printer.py               │
│   parametres                  │  │   file_io.py               │
│                               │  └────────────────────────────┘
│   plats/{pizza,grillade,...}  │
└───────────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────────┐
│              DONNÉES (dossier data/ configurable)             │
│  config.json · stock.json · carte_active.json                 │
│  carte_archive.json · commandes/{en_cours,terminee,annulee}/  │
│  logs/app_YYYYMMDD.log · logs/derniers_ID.json                │
└───────────────────────────────────────────────────────────────┘
```

**Application légère postes cuisine** (`src/core/app_prep.py` + `src/UI_prep/`) : point d'entrée alternatif sans dépendance USB ni modules de gestion (stock, carte, logs, historique). Conçu pour des machines à 4 Go de RAM sur réseau LAN.

### Principes architecturaux

- **Découplage UI/backend** : les modules UI n'accèdent jamais directement aux fichiers — ils passent par `data_sources.py` ou les helpers de `commandes_utils.py`.
- **Singleton de cache** : `StockCache` et `DerniersIDCache` sont des singletons en mémoire, persistés sur disque uniquement aux points de validation (validation d'une commande, annulation).
- **Signaux Qt** : la communication entre modules passe par des signaux (`command_changed`, `config_changed`, `go_back`…) sans couplage direct.
- **Rafraîchissement par timer** : les vues saisie (2 s), suivi (5 s) et extérieur (3 s) se rechargent périodiquement depuis le disque pour refléter les modifications d'autres modules. Les modules non visibles ne rechargent pas leurs données tant qu'ils ne sont pas affichés (optimisation disque).
- **Routage des plats** : le système `plats_router.py` + `rooting.py` par type de plat permet d'ajouter un nouveau type de plat sans modifier le code de saisie de commande.

---

## 4. Structure des fichiers de données

Tous les chemins sont dérivés d'un **dossier data unique**, configurable dans les paramètres.

```
data/
├── config.json               # Configuration applicative (lue depuis assets/)
├── stock.json                # Inventaire hiérarchique
├── carte_active.json         # Carte en service (catégories, recettes, prix, états)
├── carte_archive.json        # Carte archive (backup / gestion historique)
├── commandes/
│   ├── commande_YYYYMMDD-NNN.json   # Brouillon en cours de saisie (racine)
│   ├── en_cours/
│   │   └── commande_*.json          # Commandes validées, plats en préparation/prêts
│   ├── terminee/
│   │   └── commande_*.json          # Commandes complètement livrées
│   ├── annulee/
│   │   └── commande_*.json          # Commandes entièrement annulées
│   └── corrompu/
│       └── commande_*.json          # Fichiers JSON invalides (mis en quarantaine)
└── logs/
    ├── app_YYYYMMDD.log      # Journal applicatif journalier (JSON Lines)
    └── derniers_ID.json      # Cache des compteurs d'IDs du jour
```

### Structure d'un fichier de commande

```json
{
  "Informations": {
    "ID": "20260612-007",
    "Date de création": ["12/06/2026", "14:32"],
    "Date de validation": ["12/06/2026", "14:35"],
    "Date de finalisation": ["12/06/2026", "14:50"],
    "Statut": "Terminée",
    "Montant": 12.50,
    "Devise": "EUR",
    "Type de paiement": "Carte",
    "Prioritaire": false,
    "Contact": ""
  },
  "Commande": {
    "P001": {
      "ID": "20260612-007-P001",
      "Plat": "Pizza",
      "Recette": "4 Fromages",
      "Nom": "Pizza 4 Fromages — Base blanche",
      "Date de mise en livraison": ["12/06/2026", "14:48"],
      "Date de livraison": ["12/06/2026", "14:50"],
      "Statut": "Livré",
      "Prix": 8.50,
      "Composition": {
        "Base": "Crème fraîche",
        "Ingrédients": ["Mozzarella", "Emmental", "Chèvre", "Roquefort"]
      }
    }
  }
}
```

### Statuts possibles d'une commande

| Statut | Emplacement fichier |
|---|---|
| `En saisie` | Racine `commandes/` |
| `Validée` / `En cours` | `commandes/en_cours/` |
| `Terminée` | `commandes/terminee/` |
| `Annulée` | `commandes/annulee/` |

### Statuts possibles d'un plat

`En attente` → `En préparation` → `Prêt` → `Livré`
`En attente` / `En préparation` / `Prêt` → `Annulé`
`Prêt` → `Non livré` (si annulé sans candidat de transfert)
`Prêt` → `En préparation` (correction d'erreur, via `retour_preparation`)
`Livré` → `Prêt` (correction d'erreur, via `retour_pret`)

---

## 5. Couche `core`

### `src/core/version.py`

**Version centralisée.** Définit la constante `APP_VERSION` utilisée pour l'affichage et la vérification des mises à jour.

---

### `src/core/app.py`

**Point d'entrée principal.** Lance l'application PySide6 avec le thème sombre.

| Fonction | Description |
|---|---|
| `_build_dark_palette() → QPalette` | Construit la palette de couleurs sombres (fond `#2f3136`, texte `#f5f5f5`, accent bleu `#2a82da`) utilisée par toute l'application via le style Fusion. |
| `__main__` | Instancie `QApplication`, applique le style Fusion + palette sombre, définit l'icône (`logo_snack.svg`), enregistre les événements de démarrage/arrêt, crée et affiche `MainWindow`. |

---

### `src/core/app_prep.py`

**Point d'entrée allégé pour postes cuisine.** Lance une version minimale de l'application sans dépendances USB ni modules de gestion (stock, carte, logs, historique, impression). Conçu pour des machines à ressources limitées (≥ 4 Go RAM).

| Fonction | Description |
|---|---|
| `__main__` | Instancie `QApplication` avec le même thème sombre, crée et affiche `MainWindowPrep`. Aucun import `escpos`/`pyusb`. |

---

## 6. Couche `UI`

### `src/UI/main_window.py`

**Fenêtre principale** (`QMainWindow`). Orchestre les fenêtres secondaires et la bannière de mise à jour.

| Méthode | Description |
|---|---|
| `__init__` | Initialise la fenêtre (titre, taille 1200×800, icône SVG), crée `InterfacePrincipaleWidget` comme widget central, crée `SuiviExterieurWindow` (masquée par défaut), lance `UpdateChecker`. |
| `setup_shortcuts()` | Enregistre les raccourcis globaux : `Ctrl+Q` (quitter), `F11` (plein écran), `Escape` (quitter plein écran), `Ctrl+M` (minimiser). |
| `_on_update_available(version)` | Reçoit le signal de `UpdateChecker` et insère une bannière non-bloquante en haut de la fenêtre. |
| `_toggle_suivi_exterieur(checked)` | Affiche ou masque `SuiviExterieurWindow`. Journalise l'événement `AFFICHAGE_EXTERIEUR`. |
| `toggle_fullscreen()` | Bascule entre `showNormal()` et `showFullScreen()`. |
| `exit_fullscreen()` | Quitte le plein écran si actif. |
| `closeEvent(event)` | Ferme proprement `SuiviExterieurWindow` (via `force_close()`) avant de quitter. |

---

### `src/UI/module_registry.py`

**Registre de découverte dynamique des modules UI.** Permet d'ajouter un module sans modifier le code central — il suffit de créer un dossier dans `src/modules/` avec un `module.py` optionnel.

| Fonction | Description |
|---|---|
| `_normalize_text(value) → str` | Normalise une chaîne en identifiant ASCII minuscule sans ponctuation (suppression des accents, caractères spéciaux). |
| `_load_module(module_path) → module` | Charge dynamiquement un fichier Python via `importlib.util` et retourne le module, ou `None` en cas d'échec. |
| `_pick_icon(folder) → Optional[str]` | Retourne le chemin de la première icône trouvée (`icon.svg` ou `icon.png`) dans le dossier d'un module. |
| `discover_module_registry() → Dict` | Parcourt `src/modules/`, charge le `module.py` si présent (cherche `get_module_descriptor()` ou les constantes `LABEL`, `ICON_PATH`…), et construit un registre indexé par label normalisé et par slug. |

---

### `src/UI/utils/icones.py`

**Utilitaires de rendu d'icônes SVG**, partagés par tous les écrans qui chargent des icônes depuis `assets/icons/` (volet de navigation, historique, saisie de commande, paiement, boutons plats, logs, paramètres). Centralise un problème récurrent : les SVG sources ont des marges/viewBox incohérents, ce qui donnait des icônes de tailles et de centrages différents selon le fichier une fois rastérisées.

| Fonction | Description |
|---|---|
| `_rect_trace_opaque(image) → QRect` | Calcule le rectangle englobant des pixels non transparents d'une image, pour recadrer sur le tracé réel plutôt que sur le viewBox brut. |
| `pixmap_depuis_svg(chemin_svg, taille, *, recadrer=True) → QPixmap` | Rend un SVG (chemin arbitraire), recadré et mis à l'échelle/centré dans `taille` (`int` pour un carré, `QSize` pour un rectangle libre, ex. logo), sans recoloration. |
| `icone(nom_fichier, taille, *, recadrer=True) → QIcon` | Charge une icône depuis `assets/icons/`, sans recoloration. |
| `icone_coloree(nom_fichier, couleur, taille, *, recadrer=True) → QIcon` | Charge une icône depuis `assets/icons/`, recolorée en aplat (lisibilité sur fond sombre ou clair). |
| `icone_action(nom_fichier, taille, couleur_normale, couleur_desactivee, *, recadrer=True) → QIcon` | Variante à deux états (`QIcon.Mode.Normal` / `Disabled`), pour les boutons d'action dont l'icône doit s'effacer visuellement une fois désactivés (ex. annulation). |

---

### `src/UI/view/volet_navigation.py`

**Volet de navigation latéral tactile.** Remplace la `QMenuBar` classique. S'affiche en superposition sur le contenu principal.

| Élément / Méthode | Description |
|---|---|
| `VoletNavigation` | Widget glissant affiché/masqué par un bouton hamburger. Fond sombre `#1e2124`, largeur fixe. |
| Boutons de navigation | Un bouton par module (icône + label), hauteur 50 px. L'item actif est mis en évidence (fond bleu `#4a7fcb`, gras). |
| Bouton "Quitter" | Style danger (texte rouge), séparé des liens de navigation. |
| Raccourcis | `F11` / `Escape` pour basculer le plein écran depuis le volet. |

---

### `src/UI/view/interface_principale.py`

**Assembleur de la vue principale.** Gère le `QStackedWidget` gauche (7 pages) et le panneau de suivi droit.

| Élément / Méthode | Description |
|---|---|
| `_PAGES_MODE_SPLIT` | Frozenset `{"saisie"}` — seule la page saisie affiche le panneau suivi à droite. |
| `PlaceholderPage` | Widget générique affichant un titre et un message, utilisé pour les pages non encore implémentées. |
| `InterfacePrincipaleWidget.__init__` | Construit les 7 pages du stack (`SaisieCommandeModule`, `StockModule`, `CarteModule`, `CommandesHistoriqueModule`, `LogsModule`, `ParametresModule`, `PostePreparationModule`) et le `SuiviCommandesModule`. Intègre `VoletNavigation` en superposition. Connecte les signaux inter-modules (`config_changed → refresh_all_pages`, `command_changed → refresh_all_pages`, `go_back → saisie`, etc.). Démarre sur la page **Paramètres**. |
| `set_left_page(page_name)` | Affiche la page demandée dans le stack, appelle `_refresh_page`, et adapte la visibilité du panneau suivi (mode split uniquement pour `"saisie"`). |
| `refresh_all_pages()` | Rafraîchit toutes les pages du stack et le suivi (appelé sur `config_changed` ou `command_changed`). |
| `_refresh_page(widget)` | Appelle `refresh()`, `reload_from_disk()` ou `refresh_orders()` selon ce que le widget expose. |

---

### `src/UI/suivi_exterieur_window.py`

**Fenêtre secondaire publique** (`QMainWindow`) affichant les commandes prêtes et en préparation, destinée à un écran client.

| Élément / Méthode | Description |
|---|---|
| `_MAX_EN_PREP_PAR_TYPE = 3` | Constante limitant l'affichage à 3 plats par type dans la section "En préparation". |
| `SuiviExterieurWindow.__init__` | Construit l'UI, configure les raccourcis F11/Escape, démarre un timer de 3 secondes et appelle `refresh()`. |
| `_build_ui()` | Crée un scroll area avec deux sections (Prêts / En préparation). |
| `_build_timer()` | Timer toutes les 3 s → `refresh()`. |
| `refresh()` | Recharge les plats via `get_live_orders_prep()`, sépare Prêts / En préparation, regroupe par type (max 3 par type), reconstruit l'affichage. |
| `_build_section_prêts(prêts)` | Construit le cadre vert "✓ Prêts à récupérer" avec la liste des plats. |
| `_build_section_prep(prep_par_type)` | Construit le cadre orange "⏳ En préparation" avec les plats groupés par type. |
| `_build_plat_row(plat, style)` | Construit une ligne (type du plat + numéro de commande). |
| `force_close()` | Arrête le timer et ferme la fenêtre définitivement (appelé par `MainWindow.closeEvent`). |
| `closeEvent(event)` | Masque la fenêtre (fermeture manuelle) en émettant `closed`, ou la détruit si `_app_closing=True`. |

---

### `src/UI_prep/` — Interface allégée pour postes cuisine

Module UI dédié à `app_prep.py`. N'importe aucun module de gestion (stock, historique, carte, logs, impression).

#### `main_window_prep.py` — `MainWindowPrep`

Fenêtre principale de l'application légère. Contient `PostePreparationModule` comme widget central et intègre `PanneauLateral`.

#### `panneau_lateral.py` — `PanneauLateral`

Volet de configuration minimal accessible depuis un bouton flottant.

| Élément | Description |
|---|---|
| Sélecteur dossier data | `QFileDialog` pour pointer vers un partage réseau LAN. Rafraîchit `PostePreparationModule` instantanément. |
| Logo MegaSnack | `QSvgWidget` affiché en en-tête du panneau. |
| Plein écran | Bascule `showFullScreen` / `showNormal`. |
| Quitter | Ferme proprement l'application. |

---

## 7. Couche `backend`

### `src/backend/file_io.py`

**Accès bas niveau aux fichiers JSON partagés en LAN.** Plusieurs postes (caisse, cuisine, suivi…) peuvent lire et écrire les mêmes fichiers (stock, commandes, IDs journaliers) depuis le réseau local. Ce module garantit l'écriture atomique (fichier temporaire + `os.replace`) et le verrouillage inter-processus/inter-machine via `filelock`, pour éviter qu'un crash laisse un JSON à moitié écrit ou que deux postes s'écrasent mutuellement leurs modifications.

| Fonction | Description |
|---|---|
| `verrou_fichier(chemin)` | Retourne un `FileLock` (timeout 15 s) sur le fichier `<chemin>.lock` associé. |
| `charger_json(chemin)` | Charge un JSON et retourne `{}` si absent ou invalide. |
| `sauvegarder_json(chemin, payload)` | Écrit un dict en JSON de façon atomique, sans verrou — pour une écriture isolée par un seul poste. |
| `acceder_json(chemin)` | Context manager : verrouille, charge la dernière version sur disque, fournit le dict pour modification, puis sauvegarde atomiquement en sortie de bloc. À utiliser pour toute séquence "charger → modifier → sauvegarder" sur un fichier partagé. Ne sauvegarde rien si une exception est levée dans le bloc. |

---

### `src/backend/app_config.py`

**Gestion de la configuration applicative.** Source unique de vérité pour tous les chemins de fichiers.

| Constante / Fonction | Description |
|---|---|
| `CONFIG_FILE` | Chemin vers `assets/config.json` (fichier de configuration applicative). |
| `STOCK_FILENAME`, `CARTE_ACTIVE_FILENAME`, etc. | Noms de fichiers fixes dans le dossier data. |
| `_DEFAULT_PRINTER` | Valeurs par défaut imprimante (Epson TM-T20II, vendor `0x04B8`, product `0x0E15`). |
| `_default_data_folder()` | Retourne `PROJECT_ROOT/data` en développement, ou le dossier à côté de l'exécutable si compilé (PyInstaller). |
| `_load_json_file(file_path)` | Charge un JSON et retourne `{}` si absent ou invalide — ne lève jamais d'exception. |
| `_write_json_file(file_path, payload)` | Écrit un dict JSON en créant les dossiers parents. Retourne `True` si succès. |
| `data_folder_est_configure()` | Retourne `True` si un chemin non vide a été explicitement défini dans `config.json`. |
| `get_data_folder_brut()` | Retourne le chemin tel que saisi dans `config.json`, ou `""` si absent/vide. |
| `get_data_folder()` | Retourne `get_data_folder_brut()` si défini, sinon le dossier par défaut. |
| `get_stock_file_path()` | `get_data_folder() / "stock.json"` |
| `get_menu_file_path()` | `get_data_folder() / "carte_active.json"` |
| `get_archive_menu_file_path()` | `get_data_folder() / "carte_archive.json"` |
| `get_archive_folder_path()` | `get_data_folder() / "commandes"` |
| `get_logs_folder_path()` | `get_data_folder() / "logs"` |
| `get_command_root()` | Retourne le dossier commandes s'il existe, `None` sinon. |
| `_parse_hex_or_int(value, default)` | Convertit `"0x04B8"` ou un entier en `int`. |
| `get_printer_config()` | Lit et retourne la config imprimante avec valeurs par défaut si absente. |
| `get_print_options()` | Retourne `{impression_active, ticket_client, ticket_cuisine}` — tous `True` par défaut. |
| `_create_data_structure(data_folder)` | Crée récursivement la structure `commandes/{en_cours,terminee,annulee,corrompu}`, `logs/`, et les fichiers JSON vides. Journalise chaque création. |
| `initialiser_dossier_data()` | Crée la structure du dossier data si un chemin est configuré. Ne fait rien (retourne `True`) si `data_folder` est vide. |
| `save_app_config(data_folder, vendor_id, ...)` | Persiste toute la configuration dans `config.json`. Appelle `_create_data_structure` uniquement si `data_folder` est non vide. Retourne `True` si succès. |
| `get_default_config()` | Retourne la configuration par défaut (`data_folder: ""`). |

---

### `src/backend/data_sources.py`

**Sources de données métier.** Chargement/sauvegarde centralisé de la carte, du stock et des commandes. Fournit les catégories enrichies (icône, état, recettes) aux vues de saisie.

| Fonction | Description |
|---|---|
| `get_card_data()` | Charge `carte_active.json`. |
| `save_card_data(payload)` | Sauvegarde `carte_active.json`. |
| `get_archive_card_data()` | Charge `carte_archive.json`. |
| `save_archive_card_data(payload)` | Sauvegarde `carte_archive.json`. |
| `get_stock_data()` | Charge `stock.json` directement depuis le disque. |
| `save_stock_data(payload)` | Sauvegarde `stock.json` directement. |
| `_reconcilier_brouillons(cache)` | Au démarrage, décrémente le cache pour les plats "En attente" des brouillons existants (commandes "En saisie" en racine) pour compenser un arrêt brutal précédent. |
| `get_stock_cache()` | Retourne le singleton `StockCache`. Le crée au premier appel (charge le JSON + réconcilie les brouillons). |
| `invalider_cache_stock()` | Remet le singleton à `None`. À appeler quand le dossier de données change : le prochain appel à `get_stock_cache()` recrée un cache pointant sur le nouveau chemin. |
| `_normalize_text(value)` | Normalise ASCII minuscule sans ponctuation. |
| `_normalized_state(state)` | Normalise l'état d'une catégorie pour comparaison insensible à la casse et aux accents. |
| `_find_category_folder(category_name)` | Cherche le dossier `src/modules/<nom normalisé>` correspondant à une catégorie. |
| `_resolve_category_icon(category_name, out_of_stock)` | Retourne le chemin `icon.svg` du module correspondant à la catégorie. |
| `get_menu_categories()` | Retourne la liste des catégories de la carte active enrichies : `name`, `state`, `price`, `recipe_count`, `has_recipes`, `hidden`, `out_of_stock`, `enabled`, `icon_path`. Les catégories `"Retiré"` et `"Archivé"` sont masquées. |
| `get_draft_orders()` | Charge les commandes "En saisie" depuis la racine du dossier commandes (max 1 brouillon). Retourne une liste de dicts avec `file, id, status, created_at, items, amount, priority`. |
| `_parse_order_file(order_file)` | Charge et structure un fichier JSON de commande → `(infos, command_lines)`. |
| `get_live_orders()` | Charge les commandes en cours depuis `en_cours/`. Retourne les compteurs `active_count`, `pending_count`, `delivered_count`, `cancelled_count` par commande. |
| `get_live_orders_prep()` | Charge les commandes `en_cours/` et retourne une **liste plate** de plats (un dict par plat) excluant Annulé/Livré/Non livré. Utilisé par le poste cuisine et l'affichage extérieur. |
| `get_all_history_orders()` | Charge toutes les commandes depuis `en_cours/`, `terminee/` et `annulee/`, triées par ID décroissant. Utilisé par l'historique. |
| `get_completed_orders()` | Charge uniquement les commandes terminées depuis `terminee/`. |

---

### `src/backend/commandes_utils.py`

**Utilitaires de gestion des commandes.** Cache des identifiants journaliers, restauration stock, recherche de candidat de transfert.

#### Classe `DerniersIDCache`

Cache mémoire des compteurs d'IDs journaliers. Persisté dans `logs/derniers_ID.json`.

| Attribut / Méthode | Description |
|---|---|
| `_FILENAME = "derniers_ID.json"` | Nom du fichier de persistance. Supporte la migration depuis l'ancien `dernier_id.json`. |
| `__init__(logs_path)` | Charge les compteurs depuis le fichier existant. Les compteurs de plats sont indexés par lettre (`"P"`, `"G"`, `"F"`, `"S"`, `"C"`) depuis la migration, pas par nom de type. Gère deux migrations transparentes : ancien format entier `{"20260606": 8}` → `{"commande": N, ...}` ; anciennes clés par nom (`"pizza"`) → clés par lettre (`"P"`). |
| `save()` | Persiste les compteurs sur disque. |
| `prochain_id_commande()` | Incrémente le compteur commande, persiste et retourne `"YYYYMMDD-NNN"`. |
| `decrementer_commande()` | Décrémente le compteur commande (annulation d'une commande en saisie). |
| `prochain_id_plat(type_plat)` | Incrémente le compteur du type, persiste et retourne `"X000"` (ex. `"P001"`). Résout le préfixe depuis `PREFIXES_PLAT`, puis `Lettre_ID` dans la carte active, puis `"X"` en repli. |

#### Fonctions utilitaires

| Fonction | Description |
|---|---|
| `get_id_cache()` | Retourne le singleton `DerniersIDCache`. Recrée automatiquement si le jour a changé (passage minuit). |
| `generer_ID_commande()` | Délègue à `get_id_cache().prochain_id_commande()`. |
| `generer_ID_plat(type_plat)` | Délègue à `get_id_cache().prochain_id_plat()`. |
| `decrementer_ID_commande()` | Délègue à `get_id_cache().decrementer_commande()`. |
| `restaurer_stock_plat(plat)` | Restitue dans le cache stock les quantités consommées par un plat annulé (Pizza : +1 pâte ; Grillade : +N pour chaque viande). |
| `log_stock_restauration(plat, id_commande)` | Journalise la restauration automatique de stock dans le log `MODIFICATION_CACHE_STOCK`. |
| `plats_identiques(plat_ref, plat_candidat)` | Vérifie l'égalité stricte type + recette + nom + composition entre deux plats. |
| `trouver_candidat_transfert(plat_ref, chemin_commande_source)` | Cherche dans toutes les commandes `en_cours/` un plat identique "En préparation" à qui transférer l'état "Prêt". Ordre de priorité : même commande → commandes prioritaires → autres. |
| `charger_fichier_commande(chemin_fichier)` | Charge un fichier JSON de commande. En cas de JSON invalide, déplace le fichier vers `corrompu/` et journalise `FICHIER_CORROMPU`. |

---

### `src/backend/logger.py`

**Système de journalisation applicative.** Fichiers JSON Lines journaliers (`data/logs/app_YYYYMMDD.log`).

#### Constantes d'événements

| Catégorie | Événements |
|---|---|
| `commande` | `AJOUT_PLAT`, `ANNULATION_PLAT`, `ANNULATION_COMMANDE`, `VALIDATION_COMMANDE`, `PLAT_PRET`, `PLAT_LIVRE`, `PLAT_NON_LIVRE`, `TRANSFERT_PRET`, `COMMANDE_TERMINEE`, `IMPRESSION_TICKET`, `RETOUR_PREPARATION`, `RETOUR_PRET`, `COMMANDE_ROUVERTE` |
| `stock` | `MODIFICATION_STOCK_MANUELLE`, `MODIFICATION_CACHE_STOCK`, `PERSISTANCE_STOCK` |
| `carte` | `MODIFICATION_CARTE_MANUELLE` |
| `parametres` | `MODIFICATION_PARAMETRES_IMPRIMANTE`, `MODIFICATION_OPTIONS_IMPRESSION`, `MODIFICATION_DOSSIER_DONNEES` |
| `systeme` | `DEMARRAGE_APP`, `ARRET_APP`, `CREATION_DOSSIER`, `CREATION_FICHIER`, `FICHIER_CORROMPU`, `AFFICHAGE_EXTERIEUR` |
| `erreur` | `ERREUR` |

#### Fonctions

| Fonction | Description |
|---|---|
| `_next_index(today, log_file)` | Retourne le prochain numéro de séquence journalier. Relit le fichier existant au premier appel du jour pour assurer la continuité après redémarrage. |
| `migrer_log_journalier(ancien_dossier, nouveau_dossier)` | Déplace ou fusionne le fichier log du jour lors d'un changement de dossier data. En cas de doublon, fusionne avec déduplication par `(timestamp, evenement, details)`, trie chronologiquement et réindexe. |
| `log(evenement, details)` | Enregistre une entrée JSON Lines dans `data/logs/app_YYYYMMDD.log`. Format : `{"index": N, "timestamp": "ISO", "categorie": "...", "evenement": "...", "details": {...}}`. Ne lève **jamais** d'exception — les erreurs disque sont silencieusement ignorées. |

---

### `src/backend/printer.py`

**Impression ESC-POS des tickets.** Gère l'impression automatique à la validation et la réimpression manuelle depuis l'historique.

| Fonction | Description |
|---|---|
| `charger_logo(nom_image, taille)` | Charge une image PNG ou **SVG** et la convertit en 1-bit pour l'imprimante thermique. SVG : conversion via `svglib.svg2rlg` + `renderPM.drawToString` (reportlab). PNG : redimensionnement Pillow. Dans les deux cas : composite sur fond blanc puis quantification en noir/blanc. |
| `_get_printer()` | Instancie `escpos.printer.Usb` depuis la configuration (`vendor_id`, `product_id`, `interface`, `profile`). |
| `_do_print_recap(commande, p, reprint)` | **Ticket récapitulatif client** : logo en-tête + date + N° commande (grand format) + montant + type paiement + détail de chaque plat. Si `reprint=True`, imprime tous les plats sans filtrage de statut. |
| `_print_plat_ticket(plat, infos, p)` | **Ticket cuisine par plat** : date + ID court + composition détaillée selon le type (viandes/accompagnement pour grillade, base/ingrédients pour pizza, etc.). |
| `print_ticket_recap(chemin_fichier)` | Impression automatique (appelée à la validation). Vérifie `impression_active` et `ticket_client` avant d'imprimer. Journalise `IMPRESSION_TICKET`. |
| `print_ticket_cuisine(chemin_fichier)` | Impression automatique d'un ticket par plat "En attente". Vérifie `ticket_cuisine`. |
| `reprint_ticket_recap(chemin_fichier)` | Réimpression manuelle (depuis l'historique). Contourne les options d'impression automatique. Lève `RuntimeError` si l'impression échoue. |
| `reprint_ticket_cuisine_plat(chemin_fichier, plat_id)` | Réimprime le ticket cuisine d'un seul plat identifié par son ID complet. |
| `reprint_all_active_cuisine()` | Réimprime les tickets cuisine de tous les plats `En préparation` ou `Prêt` des commandes actives. Retourne le nombre de tickets imprimés. |

---

### `src/backend/update_checker.py`

**Vérification des mises à jour disponibles.** Interroge l'API GitHub Releases en arrière-plan sans bloquer l'interface.

| Élément | Description |
|---|---|
| `_GITHUB_API_URL` | URL de l'API GitHub Releases pour le dépôt `dracudar/morphoz_snackapp`. |
| `_parse_version(v)` | Convertit `"v2.1.0"` en tuple `(2, 1, 0)` pour comparaison sémantique. |
| `UpdateChecker(QThread)` | Thread Qt qui effectue la requête HTTP (timeout 5 s). Émet `update_available(str)` si la version distante est supérieure à `current_version`. Ne lève jamais d'exception — les erreurs réseau sont silencieusement ignorées. |

---

## 7.bis `src/utils/`

Composants Qt réutilisables partagés entre plusieurs modules UI.

### `src/utils/tactile.py`

| Classe | Description |
|---|---|
| `ScrollAreaTactile` | `QScrollArea` avec défilement cinétique tactile (geste `TouchGesture` via `QScroller`), scrollbars masquées. Expose `est_en_scroll()` pour que les boutons enfants détectent un scroll en cours. Propriétés `QScrollerProperties` ajustées (`DecelerationFactor`, `MinimumVelocity`). |
| `BoutonTactile` | `QPushButton` qui bloque l'événement `mouseReleaseEvent` si sa `ScrollAreaTactile` parente est en cours de défilement — évite les activations involontaires au scroll. Fonctionne pour les boutons checkables et les boutons d'action. |
| `EnTeteCliquable` | `QFrame` d'en-tête cliquable sur toute sa largeur. Émet `clicked()` au relâchement sauf si une `ScrollAreaTactile` englobante est en train de défiler. Hauteur minimale 44 px (recommandation tactile). |

`BoutonIngredientTactile` est conservé comme alias de `BoutonTactile` pour la rétrocompatibilité interne.

---

## 8. Modules métier

### 8.1 `commandes_saisie`

**Saisie des commandes.** Module principal de l'interface opérateur : grille de boutons par catégorie, liste de la commande en cours, paiement.

#### `UI/commande_saisie.py` — `SaisieCommandeModule`

| Méthode | Description |
|---|---|
| `_build_ui()` | Construit les deux zones : cadre menu (35 %) avec grille de boutons, et cadre détail commande (65 %) avec liste d'articles et boutons d'action. |
| `_build_menu_frame(parent_layout)` | Crée la grille scrollable de `BoutonMenu` par catégorie. |
| `_build_command_detail_frame(parent_layout)` | Crée la section titre, liste scrollable d'`ItemRow`, et boutons (Annuler / Valider / Prioritaire). |
| `_get_current_order()` | Retourne la première commande brouillon via `get_draft_orders()`. |
| `_display_no_order_state()` | État vide : titre neutre, liste vide, boutons désactivés. |
| `_display_order_state(order)` | État actif : titre `"Commande YYYYMMDD-NNN"`, articles, montant sur le bouton Valider. |
| `_refresh_items_display(order)` | Reconstruit les `ItemRow` triés par clé de plat. |
| `_handle_item_cancel(item_id)` | Appelle `annuler_plat()` et rafraîchit. |
| `_handle_toggle_priority()` | Appelle `set_prioritaire()` et émet `command_changed`. |
| `_handle_cancel_command()` | Appelle `annuler_all_plats()` et rafraîchit. |
| `_handle_validate_command()` | Ouvre `PaymentDialog` et connecte `payment_selected → _process_payment`. |
| `_process_payment(payment_type)` | Appelle `paiement_carte()`, `paiement_especes()` ou `gratuit()` selon le choix. |
| `refresh_menu()` | Relit `get_menu_categories()` et reconstruit la grille de boutons (5 colonnes). |
| `_on_category_button_clicked(category_name)` | Appelle `route_plat_selection()`, puis `MAJ_commande()` si un plat est retourné. |
| `_setup_refresh_timer()` | Timer 2 s → `_on_timer_tick()` pour rafraîchir la liste des articles. |

#### `UI/widgets/bouton_menu.py` — `BoutonMenu`

Bouton carré (100×100) avec icône SVG colorée et label. Supporte les états normal/désactivé/hover/pressed avec palettes de couleur adaptées.

#### `UI/widgets/item_row.py` — `ItemRow`

Ligne de commande affichant le nom du plat, son statut coloré et un bouton d'annulation. Émet `item_cancelled(item_id)`.

| Fonction | Description |
|---|---|
| `extract_plat_sort_key(plat_id)` | Extrait `(lettre, numéro)` depuis `"YYYYMMDD-NNN-X000"` pour le tri. |

#### `UI/payment_dialog.py` — `PaymentDialog`

Dialogue modal de sélection du mode de paiement. Émet `payment_selected(str)` avec `"Carte"`, `"Espèces"` ou `"Gratuit"`.

#### `backend/gestion.py`

| Fonction | Description |
|---|---|
| `set_prioritaire(chemin, valeur)` | Met `Informations.Prioritaire` à `True`/`False` dans le JSON de commande. |
| `valider_commande(chemin)` | Enregistre la date de validation, appelle l'impression, passe les plats "En attente" → "En préparation", persiste le cache stock et les IDs, déplace le fichier vers `en_cours/`. |
| `annuler_commande(chemin)` | Pour une commande validée : marque "Annulée" si tous les plats sont annulés, déplace vers `annulee/`. |
| `annuler_plat(chemin, plat_id)` | **Branche saisie** (statut "En saisie" + plat "En attente") : restaure le stock, supprime la clé du plat. Si la commande est vide, supprime le fichier et décrémente l'ID commande. **Branche validée** : marque "Annulé" avec horodatage `Date d'annulation`, restaure le stock si "En attente" ou "En préparation", appelle `annuler_commande()`. |
| `annuler_all_plats(chemin)` | Annule tous les plats. En saisie : restaure le stock de chaque plat, supprime le fichier et décrémente l'ID commande. Validée : appelle `annuler_plat` pour chaque plat. |

#### `backend/saver.py`

| Fonction | Description |
|---|---|
| `initialiser_dossiers_commandes(commandes_path, logs_path)` | Crée la structure de dossiers nécessaire avant toute sauvegarde. |
| `creer_dict_plat(plat_id, plat)` | Construit le dictionnaire d'un plat. Pour les pizzas, insère `"Recette"` entre `"Plat"` et `"Nom"` via `OrderedDict`. |
| `_sort_key_plat(id_type)` | Retourne `(lettre, numéro)` pour trier les plats (`"P030"` → `('P', 30)`). |
| `_log_stock_ajout(plat, plat_id, id_commande)` | Journalise le décrément de stock lors de l'ajout d'un plat (Pizza : -1 pâte ; Grillade : -N viandes). |
| `MAJ_commande(commandes_path, logs_path, plat)` | **Fonction centrale de saisie.** Si un brouillon existe, y ajoute le plat (génère l'ID type, calcule le montant, trie les plats). Sinon, crée un nouveau fichier de commande avec l'ID journalier. Journalise `AJOUT_PLAT`. |

#### `backend/paiements.py`

| Fonction | Description |
|---|---|
| `paiement_carte(chemin)` | Met `Type de paiement = "Carte"` et appelle `valider_commande()`. |
| `paiement_especes(chemin)` | Met `Type de paiement = "Espèces"` et appelle `valider_commande()`. |
| `gratuit(chemin)` | Met `Type de paiement = "Repas gratuit"` et appelle `valider_commande()`. |

#### `utils/plats_router.py`

| Élément | Description |
|---|---|
| `PLAT_HANDLERS` | Dict de routage `{"Pizza": "src.modules.plats.pizza.rooting", ...}` pour les 5 types de plats. |
| `route_plat_selection(plat_name, context, command_path)` | Charge dynamiquement le module `rooting.py` du type et appelle `route_selection()`. Journalise `ERREUR` si le type est inconnu ou si une exception est levée. |

---

### 8.2 `commandes_suivi`

**Suivi en temps réel des commandes en cours.** Panneau droit affiché uniquement en mode saisie.

#### `UI/UI.py` — `SuiviCommandesModule`

Wrapper minimal : instancie `ConteneurSuiviCommandes` et expose `tracker` pour le rafraîchissement externe.

#### `UI/widgets/conteneur_suivi_commande.py` — `ConteneurSuiviCommandes`

Affiche la liste des commandes `en_cours/` avec boutons de changement de statut par plat. Timer de rafraîchissement automatique.

#### `backend/commandes_suivi_gestion.py`

Gestion des transitions de statut pour les commandes validées.

| Fonction | Description |
|---|---|
| `_trouver_cle_plat(commande_data, plat_id_complet)` | Retourne la clé JSON (`"P001"`) d'un plat depuis son ID complet (`"YYYYMMDD-NNN-P001"`). |
| `plat_prêt(context, chemin, plat_id, callback)` | Passe un plat "En préparation" → "Prêt", horodate `Date de mise en livraison`, journalise `PLAT_PRET`, appelle le callback d'affichage. |
| `livrer_plat(context, chemin, plat_id, callback)` | Passe un plat "Prêt" → "Livré", horodate `Date de livraison`, appelle `terminer_commande()`. |
| `terminer_commande(chemin)` | Si tous les plats sont dans un état terminal (Livré, Annulé, Non livré), marque la commande "Terminée", définit `Date de livraison` (date du dernier plat livré) et déplace vers `terminee/`. |
| `marquer_plat_pret(chemin, plat_id)` | Variante sans callback (depuis l'historique). |
| `marquer_plat_livre(chemin, plat_id)` | Variante sans callback (depuis l'historique). |
| `_marquer_non_livre(commande_data, plat_key, chemin)` | Marque "Non livré" avec horodatage `Date d'annulation`. |
| `_transferer_pret(plat_data, chemin_source)` | Tente de transférer "Prêt" vers un plat identique "En préparation" (via `trouver_candidat_transfert`). Retourne `True` si transfert effectué. |
| `annuler_plat_valide(chemin, plat_id)` | Annulation d'un plat post-validation selon son statut : "En préparation" → restaure stock + "Annulé" ; "Prêt" → tente transfert ou "Non livré" ; autre → "Annulé". Appelle `_finaliser_apres_annulation`. |
| `annuler_commande_complete(chemin)` | Annule tous les plats actifs d'une commande validée en appliquant la logique unitaire. |
| `_finaliser_apres_annulation(chemin)` | Si tous les plats sont en état terminal : "Annulée" (avec horodatage `Date d'annulation`) si tous Annulés, "Terminée" (via `terminer_commande`) sinon. |
| `retour_preparation(context, chemin, plat_id, callback)` | Ramène un plat "Prêt" → "En préparation" (correction d'erreur cuisine). Journalise `RETOUR_PREPARATION`. |
| `retour_pret(chemin, plat_id)` | Ramène un plat "Livré" → "Prêt" (correction d'erreur). Si la commande était "Terminée", la rouvre ("Validée") et déplace le fichier vers `en_cours/`. Journalise `RETOUR_PRET` et `COMMANDE_ROUVERTE` le cas échéant. |

---

### 8.3 `commandes_historique`

**Historique des commandes.** Vue consultable avec recherche, filtres avancés, tri, et actions de réimpression et de changement de statut.

#### `UI.py` — `CommandesHistoriqueModule`

Affiche toutes les commandes (`en_cours`, `terminee`, `annulee`) sous forme de cartes repliables. Chaque carte de commande contient une sous-carte par plat avec les boutons d'action disponibles selon le statut.

Fonctionnalités :
- Recherche libre (filtre en temps réel sur ID, type de plat, statut).
- Filtres avancés dans `FiltreHistoriqueDialog` (statut, période, type de plat, prioritaire).
- Tri par date décroissante/croissante, montant, ID.
- Boutons plat : → Prêt, → Livré, ← Prêt (retour depuis Livré), ← En préparation (retour depuis Prêt), Annuler (avec icônes SVG colorées), réimprimer ticket cuisine.
- Bouton commande : réimprimer ticket récap, annuler commande complète.
- Bouton global "Réimprimer cuisine" (tous les plats actifs).
- Signal `go_back` pour retourner à la saisie.
- Timer 30 s de rafraîchissement automatique.

#### `filtre_dialog.py` — `FiltreHistoriqueDialog`

Dialogue de filtres avancés : statut (multi-select), période (date début/fin), type de plat (multi-select), commandes prioritaires uniquement. Retourne les critères appliqués via `filters_applied` signal.

---

### 8.4 `commandes_poste_preparation`

**Poste de préparation cuisine.** Vue plein écran pour la cuisine, affichant les plats actifs.

#### `UI/poste_preparation.py` — `PostePreparationModule`

Affiche les plats depuis `get_live_orders_prep()`, filtrable par type. Signaux `go_back` et `go_to_saisie`. Timer de rafraîchissement. Bouton de retour "Prêt → En préparation" sur chaque carte plat.

#### `UI/widgets/carte_plat.py` — `CartePlatWidget`

Widget carte d'un plat avec ID commande, type, nom, composition et statut coloré.

---

### 8.5 `plats`

**Dialogues de personnalisation par type de plat.** Architecture uniforme : chaque sous-module expose un `rooting.py` avec `route_selection(context, command_path) → Optional[Dict]`.

#### `plats/pizza/`

| Fichier | Description |
|---|---|
| `pizza_dialog.py` — `PizzaDialog` | Dialogue en 2 étapes : étape 1 sélection de la recette (grille de boutons radio), étape 2 personnalisation de la base (radio depuis le stock) et des ingrédients par catégorie (checkboxes). Retourne `result_data` avec `Plat, Recette, Nom, Prix, Statut, Composition{Base, Ingrédients}`. |
| `rooting.py` — `route_selection()` | Charge les recettes depuis `carte_active.json`, les bases et ingrédients disponibles depuis le cache stock (filtre `OutOfStock`), ouvre `PizzaDialog`, décrémente "Pâte à pizza" si confirmé. |

#### `plats/grillade/`

| Fichier | Description |
|---|---|
| `grillade_dialog.py` — `GrilladeDialog` | Sélection des viandes (quantités depuis le stock) et de l'accompagnement. Gère les contraintes de stock (désactivation si OutOfStock). |
| `rooting.py` — `route_selection()` | Charge viandes et accompagnements depuis le cache stock, ouvre le dialogue, décrémente les viandes sélectionnées dans le cache. |

#### `plats/salade_composee/`

| Fichier | Description |
|---|---|
| `salade_dialog.py` — `SaladeDialog` | Sélection des ingrédients de la salade composée (checkboxes par catégorie). |
| `rooting.py` — `route_selection()` | Ouvre le dialogue avec les ingrédients disponibles. |

#### `plats/crepe/`

| Fichier | Description |
|---|---|
| `crepe_dialog.py` — `CrepeDialog` | Sélection du type de crêpe (sucrée/salée et variante). |
| `rooting.py` — `route_selection()` | Ouvre le dialogue, retourne le dict plat. |

#### `plats/frites/`

| Fichier | Description |
|---|---|
| `rooting.py` — `route_selection()` | Retourne directement le dict plat sans dialogue (plat simple, ajout direct). |

---

### 8.6 `stock`

**Gestion des stocks.** Interface de consultation et d'édition avec cache en mémoire.

#### `UI.py` — `StockModule`

Interface en `QSplitter` 50/50 :
- **Panneau gauche** : liste hiérarchique scrollable avec barre de recherche. Articles groupés par famille (sections pliables). Chaque ligne affiche 3 tags : **Carte** (référencé dans la carte active), **Suivi** (suivi quantitatif actif), **État** (En stock / Rupture). Sélection → peuple le panneau droit.
- **Panneau droit** : formulaire d'édition de l'article sélectionné (catégorie, nom, suivi quantité ON/OFF, stock théorique, stock réel, statut OutOfStock), bouton d'enregistrement.

Fonctionnalités :
- Rechargement depuis le disque via `reload_from_disk()`.
- Détection des articles référencés dans la carte active.
- Mise à jour via le stock réel (override de la quantité et recalcul OutOfStock).
- Journalisation `MODIFICATION_STOCK_MANUELLE` à chaque sauvegarde.

#### `cache.py` — `StockCache`

| Méthode | Description |
|---|---|
| `__init__(chemin_stock_json)` | Charge le JSON et garde une copie de référence `_stock_original`. |
| `reset_cache()` | Réinitialise le cache en mémoire depuis `_stock_original`. |
| `save()` | Écrit `_stock_cache` sur disque et met à jour `_stock_original`. |
| `get_quantite(chemin)` | Lit la quantité d'un article via un chemin de clés (`["Plats", "Pizza", "Pâte à pizza"]`). |
| `decrementer(chemin, n=1)` | Décrémente de n. Active `OutOfStock = True` si la quantité atteint 0. |
| `incrementer(chemin, n=1)` | Incrémente de n. Désactive `OutOfStock` si la quantité devient positive. |
| `is_out_of_stock(chemin)` | Retourne la valeur `OutOfStock` d'un article. |
| `set_out_of_stock(chemin, valeur)` | Définit directement `OutOfStock` sans modifier la quantité. |
| `set_quantite(chemin, valeur)` | Définit directement la quantité (utilisé lors d'une mise à jour manuelle depuis l'UI). |
| `data` | Propriété retournant le dict de stock en mémoire (non copié). |

---

### 8.7 `carte`

**Gestion de la carte.** Interface d'édition des catégories (états, recettes, prix).

#### `UI.py` — `CarteModule`

Permet de modifier l'état de chaque catégorie (`Disponible`, `Rupture`, `Retiré`, `Archivé`), les recettes associées et leurs prix. Synchronise `carte_active.json` et `carte_archive.json`. Journalise `MODIFICATION_CARTE_MANUELLE`.

---

### 8.8 `parametres`

**Configuration de l'application.**

#### `UI.py` — `ParametresModule`

| Signal | Description |
|---|---|
| `config_changed` | Émis après sauvegarde d'une nouvelle configuration. Déclenche `refresh_all_pages()` dans `InterfacePrincipaleWidget`. |
| `go_back` | Émis sur le bouton retour → navigue vers la saisie. |
| `go_to_poste_prep` | Émis sur le bouton dédié → navigue vers le poste de préparation. |

Sections :
- **Données** : champ dossier data + bouton de navigation (`QFileDialog`). Info-texte sur les fichiers créés automatiquement.
- **Impression** : vendor_id, product_id, interface, modèle imprimante. Checkboxes `Impression active`, `Ticket client`, `Ticket cuisine`.

À la sauvegarde : appelle `save_app_config()` (crée la structure data si nécessaire), journalise `MODIFICATION_DOSSIER_DONNEES`, `MODIFICATION_PARAMETRES_IMPRIMANTE`, `MODIFICATION_OPTIONS_IMPRESSION`, et migre le log journalier si le dossier change (`logger.migrer_log_journalier()`).

---

### 8.9 `logs`

**Consultation du journal d'événements.**

#### `UI.py` — `LogsModule`

Lit tous les fichiers `app_*.log` du dossier logs et affiche les entrées sous forme de cartes.

| Fonction interne | Description |
|---|---|
| `_load_log_entries(logs_folder)` | Lit tous les fichiers `app_*.log` du dossier et retourne la liste des entrées JSON. |

Fonctionnalités :
- Recherche libre sur événement, catégorie, détails.
- Filtres avancés dans `FiltreTriLogDialog` : catégorie, événement exact, période (date début/fin).
- Tri par index/timestamp (ascendant/descendant).
- Badge coloré par catégorie (`commande`, `stock`, `carte`, `parametres`, `systeme`, `erreur`).
- Affichage des détails JSON de chaque entrée.
- Signal `go_back` pour retourner à la saisie.
- Timer de rafraîchissement automatique.

#### `filtre_tri_dialog.py` — `FiltreTriLogDialog`

Dialogue de filtres avancés pour le journal : sélection de catégorie(s), événement(s), plage de dates/heures, et options de tri.

#### `module.py`

Expose `get_module_descriptor()` → `{"label": "Journal", "icon_path": "...", ...}` pour le registre de modules.

---

## 9. Cycle de vie d'une commande

```
[Opérateur clique sur catégorie]
        │
        ▼
route_plat_selection()  ──►  Dialog de personnalisation (pizza_dialog, etc.)
        │                           │
        │◄──────────────────────────┘  résultat dict plat ou None
        │
        ▼
MAJ_commande()
  ├─ Brouillon existant → ajout du plat au JSON existant
  └─ Pas de brouillon  → création commande_YYYYMMDD-NNN.json (racine commandes/)
        │
        ▼
[Opérateur valide]  →  PaymentDialog
        │
        ▼
paiement_carte/especes/gratuit()
  └─ valider_commande()
       ├─ Horodate la validation
       ├─ print_ticket_recap() + print_ticket_cuisine()
       ├─ Passe plats "En attente" → "En préparation"
       ├─ StockCache.save()  (persistance stock)
       ├─ DerniersIDCache.save()  (persistance IDs)
       └─ Déplace fichier → commandes/en_cours/
            │
            ▼
   [Cuisine : plat_prêt()]
   En préparation → Prêt
            │
            ▼
   [Livraison : livrer_plat()]
   Prêt → Livré
            │
            ▼
   terminer_commande()  (si tous les plats en état terminal)
   └─ Déplace fichier → commandes/terminee/
```

### Annulation d'un plat post-validation

```
annuler_plat_valide()
  ├─ Statut "En préparation"
  │   └─ restaurer_stock_plat() + "Annulé"
  ├─ Statut "Prêt"
  │   ├─ trouver_candidat_transfert()
  │   │   ├─ Candidat trouvé → _transferer_pret() + "Annulé"
  │   │   └─ Pas de candidat → "Non livré"
  └─ Autre → "Annulé"
```

---

## 10. Système d'identifiants

### Identifiant de commande

Format : `YYYYMMDD-NNN`  
Exemple : `20260612-007` (7ème commande du 12 juin 2026)

### Identifiant de plat

Format : `YYYYMMDD-NNN-X000`  
Exemple : `20260612-007-P001` (1ère pizza de la commande 007)

| Préfixe | Type de plat |
|---|---|
| `P` | Pizza |
| `G` | Grillade |
| `F` | Frites |
| `S` | Salade composée |
| `C` | Crêpe |
| `X` | Type inconnu |

### Clé JSON dans la commande

Les plats sont stockés avec leur identifiant court comme clé JSON : `"P001"`, `"G002"`, etc.  
L'identifiant complet est stocké dans le champ `"ID"` de l'objet plat.

### Persistance

- Les compteurs sont persistés dans `logs/derniers_ID.json` à **chaque** création ou annulation d'identifiant.
- À minuit, `get_id_cache()` recrée automatiquement le cache pour le nouveau jour.
- Migration transparente depuis l'ancien format `dernier_id.json`.

---

## 11. Gestion du stock — logique cache

Le stock utilise un **double niveau** : fichier JSON (source de vérité persistée) + cache mémoire (`StockCache`).

```
Fichier stock.json  ──(lecture au démarrage)──►  StockCache._stock_original
                                                       │
                                                  deepcopy
                                                       │
                                                       ▼
                                               StockCache._stock_cache  (modifié en RAM)
                                                       │
                                        ──(save())──►  stock.json  (écrasé)
```

### Décrément automatique

À l'ajout d'un plat, le cache est décrémenté immédiatement :
- `Pizza` : −1 "Pâte à pizza"
- `Grillade` : −N pour chaque viande sélectionnée

Le cache est **persisté sur disque uniquement** à la validation d'une commande (`StockCache.save()`) ou à l'annulation d'un plat post-validation.

### Réconciliation au démarrage

Si l'application a été arrêtée brutalement avec un brouillon en cours, `_reconcilier_brouillons()` redécrémente le cache pour les plats "En attente" de ce brouillon, assurant la cohérence sans double-comptage.

### Mise à jour manuelle (module stock)

L'interface stock permet de saisir le "stock réel" : appelle `StockCache.set_quantite()` puis `StockCache.save()` pour persister immédiatement.

---

## 12. Système de journalisation

### Format d'une entrée

```json
{
  "index": 42,
  "timestamp": "2026-06-12T14:32:15",
  "categorie": "commande",
  "evenement": "VALIDATION_COMMANDE",
  "details": {
    "id_commande": "20260612-007",
    "montant": 12.50,
    "nb_plats": 2,
    "prioritaire": false
  }
}
```

### Fichier journalier

Un fichier par jour : `data/logs/app_YYYYMMDD.log`.  
Format JSON Lines : un objet JSON par ligne.  
L'index repart de 1 chaque jour et est continu (même après redémarrage).

### Migration de dossier

Lors d'un changement de dossier data dans les paramètres, `migrer_log_journalier()` déplace (ou fusionne) le fichier du jour courant, en évitant les doublons par déduplication `(timestamp, evenement, details)`.

---

## 13. Impression thermique (ESC-POS)

### Configuration imprimante

Défaut : Epson TM-T20II (`vendor_id=0x04B8`, `product_id=0x0E15`, `interface=0`).  
Configurable dans les paramètres. Valeurs stockées dans `assets/config.json`.

### Tickets générés

| Ticket | Déclencheur | Contenu |
|---|---|---|
| Récapitulatif client | Validation d'une commande | Logo en-tête · Date · N° commande (grand format) · Montant · Type paiement · Liste des plats |
| Cuisine (×N plats) | Validation d'une commande | Date · N° commande-plat · Composition détaillée |
| Réimpression récap | Bouton dans l'historique | Même contenu, tous plats sans filtre de statut |
| Réimpression cuisine plat | Bouton par plat dans l'historique | Composition du plat ciblé |
| Réimpression cuisine globale | Bouton global dans l'historique | Tous les plats actifs (En préparation / Prêt) |

### Drivers Windows

Le dossier `archive/` contient `libusb-1.0.dll` et `zadig-2.9.exe` pour l'installation du pilote USB sur Windows.

---

## 14. Assets et ressources

### `assets/config.json`

Configuration applicative (hors dossier data pour permettre la reconfiguration même si le dossier data est inaccessible).

### `assets/icons/`

| Icône | Usage |
|---|---|
| `cancel.svg` | Bouton annulation (plat ou commande) |
| `card.svg` | Tag "Carte" dans le stock |
| `coin.svg` | Paiement espèces |
| `edit.svg` | Édition |
| `exit.svg` | Quitter / retour ; bouton "Quitter" du volet de navigation |
| `filter.svg` | Bouton filtres |
| `free.svg` | Repas gratuit |
| `historique.svg` | Volet de navigation — "Historique" |
| `log.svg` | Volet de navigation — "Journal" |
| `menu.svg` | Volet de navigation — "Carte" |
| `null.svg` | Bouton plat sans icône dédiée dans son dossier `src/modules/plats/` (état vide) |
| `prepa.svg` | Volet de navigation — "Poste de préparation" |
| `print.svg` | Impression |
| `return.svg` | Retour |
| `saisie.svg` | Volet de navigation — "Saisie commande" |
| `save.svg` | Sauvegarder |
| `screen.svg` | Volet de navigation — "Plein écran" |
| `settings.svg` | Paramètres ; volet de navigation — "Paramètres" |
| `sort.svg` | Tri |
| `stock.svg` | Volet de navigation — "Stock" |
| `suivi.svg` | Volet de navigation — "Affichage extérieur" |

### `assets/imgs/`

Les images sont désormais au format **SVG** pour une qualité optimale à toutes les résolutions et tailles d'impression.

| Image | Usage |
|---|---|
| `MegaSnack.svg` | En-tête du ticket récapitulatif client + barre de navigation (rendu via `QSvgWidget` ou `svglib`) |
| `logo_snack.svg` | Icône de la fenêtre principale et de la `QApplication` |
| `logo_MegaSouye.svg` | Logo événement (réserve) |

---

## 15. Scripts utilitaires

### `scripts/printer_tickets_repas.py`

Utilitaire standalone d'impression des tickets pour les repas gratuits, indépendant de l'interface Qt. Utilisé en ligne de commande pour imprimer directement des tickets sans passer par l'application.

---

### Fichiers de compilation PyInstaller

| Fichier | Description |
|---|---|
| `morphoz_snackapp.spec` | Configuration PyInstaller pour l'application principale (`src/core/app.py`). Mode `onedir`, inclut `assets/`, `module_registry` data, `src/utils` (modules chargés uniquement via `plats_router` par import dynamique, non détectés par l'analyse statique de PyInstaller) et hidden imports USB. |
| `morphoz_prep.spec` | Configuration PyInstaller pour l'application légère (`src/core/app_prep.py`). Mode `onedir`, sans imports USB ni modules de gestion. |

Le pipeline CI/CD est scindé en deux workflows : `.github/workflows/auto-tag.yml` crée le tag `vX.Y.Z` (lu depuis `version.py`) à chaque push sur `main`, puis appelle `.github/workflows/build.yml` (workflow réutilisable, déclenché via `workflow_call`) qui compile les deux applications en parallèle sur Windows et sur Linux (matrice `x86_64` / `aarch64`, ce dernier pour cibler le Raspberry Pi 5) et publie 6 archives sur la release GitHub. Les deux étapes s'exécutent dans le même run, car un tag poussé avec le `GITHUB_TOKEN` par défaut ne déclenche pas d'autre workflow par déclenchement `push: tags:`.

---

## 16. Diagramme de dépendances simplifié

```
app.py  (application principale)
  └── MainWindow
        ├── UpdateChecker [update_checker.py]  ──► bannière notification
        ├── InterfacePrincipaleWidget
        │     ├── VoletNavigation [volet_navigation.py]
        │     ├── SaisieCommandeModule
        │     │     ├── BoutonMenu · ItemRow · PaymentDialog
        │     │     ├── route_plat_selection()
        │     │     │     └── PizzaDialog / GrilladeDialog / SaladeDialog / CrepeDialog / frites
        │     │     ├── MAJ_commande()  [saver.py]
        │     │     ├── annuler_plat() / valider_commande()  [gestion.py]
        │     │     └── paiement_*()  [paiements.py]
        │     ├── SuiviCommandesModule
        │     │     └── ConteneurSuiviCommandes
        │     │           └── plat_prêt() / livrer_plat()  [commandes_suivi_gestion.py]
        │     ├── CommandesHistoriqueModule
        │     │     ├── FiltreHistoriqueDialog
        │     │     └── marquer_plat_pret/livre/annuler_plat_valide()  [commandes_suivi_gestion.py]
        │     ├── PostePreparationModule
        │     │     └── CartePlatWidget
        │     ├── StockModule  →  StockCache  [cache.py]
        │     ├── CarteModule
        │     ├── ParametresModule  →  save_app_config()  [app_config.py]
        │     └── LogsModule
        │           └── FiltreTriLogDialog
        └── SuiviExterieurWindow  →  get_live_orders_prep()

app_prep.py  (application légère postes cuisine)
  └── MainWindowPrep [UI_prep/main_window_prep.py]
        ├── PanneauLateral [UI_prep/panneau_lateral.py]
        └── PostePreparationModule  →  get_live_orders_prep()

Couche backend (partagée par tous les modules) :
  version.py      ──► APP_VERSION
  app_config.py   ──► get_data_folder() · get_printer_config() · get_print_options()
  data_sources.py ──► get_card_data() · get_stock_cache() · get_live_orders() · ...
  commandes_utils.py ──► generer_ID_commande/plat() · restaurer_stock_plat() · ...
  logger.py       ──► log(evenement, details)
  printer.py      ──► charger_logo() (PNG+SVG) · print_ticket_recap/cuisine() · reprint_*()
  file_io.py      ──► acceder_json() · charger_json() · sauvegarder_json()
  update_checker.py ──► UpdateChecker(QThread) · update_available(Signal)
```

---

*Document mis à jour le 25/06/2026 — `APP_VERSION = "2.4.0"`.*
