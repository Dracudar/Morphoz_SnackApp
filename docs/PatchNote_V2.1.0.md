# Morphoz SnackApp — Patch Notes V2.1.0

*Version en cours de développement — premier jet*

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

## En cours de développement

- **Défilement tactile** : remplacement de tous les `QScrollArea` par un composant à défilement cinétique (idéal pour les écrans 10 pouces)
- **Logos en SVG** : conversion des images PNG (logo, en-tête ticket) en vectoriel pour une meilleure qualité d'impression

---

*Version précédente : 2.0.0 (11 juin 2026) — Réécriture complète Qt, MegaSouye 10*
