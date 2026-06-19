# Morphoz SnackApp — Patch Notes V2.1.0

*Version en cours de développement*

---

## Navigation tactile (volet latéral)

La barre de menus classique (`QMenuBar`) est remplacée par un **volet de navigation latéral** glissant, pensé pour les écrans tactiles 10 pouces :

- Volet sombre semi-transparent avec navigation par icônes et labels
- Page active mise en évidence (fond bleu, texte gras)
- `BoutonTactile` appliqué aux boutons du poste de préparation et de l'historique — distingue tap et scroll pour éviter les activations accidentelles
- En-têtes de commandes cliquables sur toute la largeur (historique)
- `QScroller` avec suivi d'état à la place du filtre global d'événements : latence tactile réduite

---

## Refonte du poste de préparation cuisine

L'affichage du poste cuisine passe d'une liste verticale à une **grille 4 colonnes** adaptée aux écrans tactiles 10 pouces :

- Cartes de plats à hauteur fixe (250 px) pour une lecture uniforme
- Badge **⚡ PRIORITAIRE** avec bordure rouge pour les commandes urgentes
- Affichage des ingrédients amélioré pour les pizzas : ingrédients standard en puces (•), ajouts en vert (+), retraits en rouge (−)
- Bouton contextuel unique qui s'adapte au statut (*Marquer Prêt* / *Livrer*)

---

## Refonte de la fenêtre d'affichage client

La fenêtre secondaire tournée vers le client est entièrement redessinée :

- Mise en page verticale : *Prêts à récupérer* en haut (plein écran), *En préparation* en bas (3 plats max par type)
- Commandes groupées **par type de plat** (Pizza, Grillade…) avec tri alphabétique
- Typographie **responsive** : tailles de police et marges s'adaptent automatiquement aux dimensions de l'écran

---

## Terminologie du cycle de vie des commandes

- "Date de livraison" renommée en **"Date de finalisation"** (sémantique plus précise)
- Ajout d'une **"Date d'annulation"** dans les commandes et les plats

---

## Logos en SVG

Les images PNG (logo, en-tête ticket) sont remplacées par des fichiers **SVG vectoriels** pour une qualité d'impression et d'affichage optimale à toutes les résolutions :

- `assets/imgs/` : `MegaSnack.svg`, `logo_snack.svg`, `logo_MegaSouye.svg` (PNG supprimés)
- Logo **MegaSnack** affiché dans la barre de navigation (via `QSvgWidget`)
- **Icône de l'application** en SVG (`logo_snack.svg`) sur la fenêtre principale et la `QApplication`
- `printer.py` utilise désormais **svglib + reportlab** pour convertir les SVG en image 1-bit avant envoi à l'imprimante thermique (remplace cairosvg)

---

## Application allégée pour postes cuisine

Un **second point d'entrée** (`src/core/app_prep.py`) permet de lancer une version réduite de l'application sur les machines à ressources limitées (4 Go RAM) :

- Charge uniquement le module **poste de préparation** — pas de stock, historique, carte, logs ni impression USB
- Panneau latéral de configuration minimal : sélecteur du dossier data (partage réseau LAN), bascule plein écran, quitter
- Logo MegaSnack en en-tête du panneau latéral

---

## Compilation et déploiement

- Fichiers **PyInstaller** `morphoz_snackapp.spec` et `morphoz_prep.spec` pour produire des exécutables autonomes Windows et Linux
- Pipeline **CI/CD GitHub Actions** (`build.yml`) : 4 builds en parallèle (Windows/Linux × app principale/app préparation), attachés automatiquement à chaque release GitHub taggée `vX.Y.Z`
- Version centralisée dans `src/core/version.py` (`APP_VERSION`)

---

## Vérificateur de mises à jour

- Au démarrage, `UpdateChecker` (QThread) interroge l'**API GitHub Releases** en arrière-plan (timeout 5 s)
- Si une version supérieure est disponible, une **bannière discrète** s'affiche en haut de la fenêtre principale — non bloquante, fermable

---

*Version précédente : 2.0.0 (11 juin 2026) — Réécriture complète Qt, MegaSouye 10*
