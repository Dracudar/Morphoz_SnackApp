# Morphoz SnackApp — Patch Notes V2.0.0

*Date de sortie : 11 juin 2026*

---

## Refonte complète de l'application

La V2.0.0 est une réécriture intégrale de l'application, développée pour l'événement **MegaSouye 10**. Le framework graphique **Tkinter** a été remplacé par **PySide6 (Qt6)**, apportant une interface moderne avec thème sombre, meilleure stabilité et une architecture modulaire extensible.

---

## Nouvelles fonctionnalités

### Poste de préparation cuisine

Affichage plein écran dédié à la cuisine, filtrable par type de plat, indépendant de l'interface de saisie.

### Fenêtre d'affichage client

Fenêtre secondaire affichant le suivi des commandes en temps réel, destinée à un écran tourné vers le client.

### Journal d'événements (module Logs)

- Consultation des logs intégrée à la navigation principale
- Enregistrement de toutes les actions : commandes, stock, paiements, paramètres, cycle de vie applicatif, erreurs
- Format JSON Lines avec indexation journalière
- Filtres et tri avancés

### Éditeur de carte

Gestion dynamique des catégories, recettes, prix et états des articles (Disponible / Rupture / Retiré / Archivé).

### Historique des commandes

Consultation avec filtres avancés (statut, date, priorité, type de plat), tri et réimpression des tickets.

---

## Modifications majeures

### Personnalisation des plats étendue

V2.0.0 ajoute des dialogs de personnalisation pour :
- Crêpe (type)
- Frites (taille)

Et améliore les dialogs existants :
- Pizza : calcul de prix dynamique selon les viandes ajoutées/retirées

### Gestion du stock : ajout d'une interface dédiée

En V1, le stock était géré uniquement en arrière-plan (cache mémoire sans UI). V2.0.0 introduit un module de gestion du stock à part entière :
- Sections repliables par famille d'articles avec compteurs et indicateurs de rupture
- Barre de recherche rapide
- Panneau de détail (valeurs Fichier / Cache / En préparation / Estimation)
- Suppression d'articles depuis l'interface
- Réconciliation du cache au démarrage si un brouillon est en suspens
- Statut *Hors service* pour les annulations post-validation

### Navigation & UX

- Architecture modulaire avec navigation latérale
- L'application démarre sur la page Paramètres lors du premier lancement
- Double bouton de navigation depuis les paramètres (Saisie / Suivi)
- Raccourcis clavier : `F11` (plein écran), `Ctrl+Q` (quitter)
- Icônes SVG pour le filtrage, le tri, l'impression et la sauvegarde

---

*Version précédente : 1.2.2 (17 juin 2025) — Interface Tkinter, MegaSouye 9*
