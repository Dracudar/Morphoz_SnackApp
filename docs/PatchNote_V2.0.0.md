# Morphoz SnackApp — Patch Notes V2.0.0

*Date de sortie : 11 juin 2026*

---

## Refonte complète de l'application

La V2.0.0 est une réécriture intégrale de l'application. Le framework graphique **Tkinter** a été remplacé par **PySide6 (Qt6)**, apportant une interface moderne avec thème sombre, meilleure stabilité et une architecture modulaire extensible.

---

## Nouveau système de gestion des commandes

- **Saisie des commandes** — Interface repensée avec support des priorités, paiement (CB, espèces, repas offert) et tickets thermiques (client + cuisine)
- **Suivi en temps réel** — Vue de suivi avec cycle de statuts : *En attente → En préparation → Prêt → Livré*
- **Poste de préparation cuisine** — Affichage plein écran dédié à la cuisine, filtrable par type de plat
- **Historique des commandes** — Consultation avec filtres avancés (statut, date, priorité, type de plat), tri et réimpression des tickets

---

## Personnalisation des plats

Boîtes de dialogue dédiées à la personnalisation de chaque type de plat :
- Pizza (recette, ingrédients, viandes avec calcul de prix dynamique)
- Grillade (choix de la viande, accompagnement)
- Salade composée (sélection des ingrédients)
- Crêpe (type)
- Frites (taille)

---

## Gestion du stock

- Sections repliables par famille d'articles (Plats, Ingrédients, Sauces…) avec compteurs et indicateurs de rupture
- Barre de recherche rapide
- Panneau de détail (suivi de quantité, valeurs Fichier / Cache / En préparation / Estimation)
- Réconciliation du cache au démarrage
- Statut *Hors service* pour les annulations post-validation
- Suppression d'articles depuis l'interface

---

## Journal d'événements (module Logs)

- Nouveau module de consultation des logs intégré à la navigation principale
- Format JSON Lines avec indexation journalière
- Catégories distinctes : commandes, stock, paiements, paramètres, cycle de vie applicatif, erreurs
- Filtres et tri avancés

---

## Carte et paramètres

- Gestion dynamique des catégories, recettes, prix et états des articles (Disponible / Rupture / Retiré / Archivé)
- L'application démarre directement sur la page Paramètres lors du premier lancement
- Configuration persistée dans `assets/config.json`

---

## Améliorations UX & navigation

- Thème sombre avec palette Qt personnalisée (style Fusion)
- Fenêtre d'affichage secondaire pour le suivi client
- Icônes SVG pour les actions de filtrage, tri, impression et sauvegarde
- Raccourcis clavier : `F11` (plein écran), `Ctrl+Q` (quitter)
- Double bouton de navigation depuis les paramètres (Saisie / Suivi)

---

*Version précédente : 1.2.2 (17 juin 2025) — Interface Tkinter*
