# Morphoz SnackApp — Patch Notes V2.0.0

*Date de sortie : 11 juin 2026*

---

## Refonte complète de l'application

La V2.0.0 est une réécriture intégrale de l'application, développée pour l'événement **MegaSouye 10**. Le framework graphique **Tkinter** a été remplacé par **PySide6 (Qt6)**, apportant une interface moderne avec thème sombre et une architecture modulaire extensible. L'ensemble des icônes PNG ont été remplacées par des icônes SVG pour un meilleur rendu haute résolution.

---

## Nouvelles fonctionnalités

### Commandes prioritaires

Ajout d'un flag priorité (!) par commande, activable depuis la saisie. Il est visible dans le panneau de suivi et sur le poste de préparation cuisine.

### Poste de préparation cuisine

Nouveau module plein écran dédié au personnel de cuisine, indépendant de l'interface de saisie :
- Affichage en grille (adapté aux écrans tactiles 10 pouces)
- Filtres par type de plat (Pizza, Grillade, Frites, Salade composée, Crêpe)
- Rafraîchissement automatique toutes les 3 secondes
- Marquage des plats *Prêt* et *Livré* directement depuis l'écran

### Historique des commandes

Nouveau module de consultation et de gestion des commandes validées :
- Barre de recherche libre permanente
- Filtres avancés : statut, période, type de plat, priorité
- Actions post-validation par plat : changement de statut, annulation, réimpression du ticket cuisine
- Actions par commande : annulation globale, réimpression du ticket récapitulatif client
- Impression groupée de tous les tickets cuisine des commandes en cours

### Éditeur de carte

Nouveau module de gestion du menu directement dans l'application (plus besoin d'éditer les fichiers JSON manuellement) :
- Arborescence des catégories et des recettes
- Formulaire d'édition : nom, prix, état (Disponible / Retiré / Hors stock), ingrédients de base, liste d'ingrédients
- Ajout, modification, suppression et rechargement depuis le disque

### Fenêtre d'affichage client

Nouvelle fenêtre indépendante en lecture seule, destinée à un écran tourné vers le public :
- Section *Prêts à récupérer* (haut, affichage complet)
- Section *En préparation* (bas, 3 plats max par type)
- Typographie responsive adaptée aux dimensions de l'écran
- Passage en plein écran (`F11`)
- Rafraîchissement automatique toutes les 2 secondes

### Journal d'événements (module Logs)

Nouveau module de consultation des journaux d'événements :
- Enregistrement de toutes les actions : commandes, stock, carte, paramètres, cycle de vie applicatif, erreurs
- Format JSON Lines avec indexation journalière
- Badges de catégorie colorés (orange, bleu, violet, vert, gris, rouge)
- Barre de recherche et filtres avancés (catégorie, événement, période, tri)

---

## Modules repris et améliorés

### Saisie des commandes

- Menu dynamique chargé depuis `carte_active.json`, affiché en grille avec icônes SVG par type de plat
- Bouton *Valider* affichant le montant en temps réel : « Valider (X.XX €) »
- Dialog de paiement unifié (un seul bouton → une fenêtre modale avec icônes SVG)
- Annulation possible plat par plat via un bouton ✕ par ligne, ou en totalité
- Ajout d'un nouveau type de plat : la **crêpe**, avec son dialog de personnalisation (choix de la garniture, calcul de prix dynamique)
- Pizza : calcul de prix dynamique selon les viandes ajoutées ou retirées

### Suivi des commandes

- Cartes de commande repliables (▶/▼) avec badges de statut colorés (orange, jaune, vert, rouge)
- Indicateur priorité (!) dans l'en-tête de chaque commande concernée
- Compteur global : nombre de commandes et de plats en cours
- Vue en lecture seule — les actions post-validation sont déplacées dans l'historique

### Gestion du stock

L'écran de stock à onglets de la V1 est remplacé par un module intégré à double panneau :
- **Panneau gauche** : liste avec sections repliables par famille, barre de recherche, et trois tags visuels par article (*Carte*, *Suivi*, *État*)
- **Panneau droit** : formulaire de détail avec valeurs Fichier / Cache / En préparation / Estimation, toggle de suivi par unité, bouton de suppression
- Compteur de préparation en temps réel (quantité en cours de préparation par article)
- Réconciliation du cache au démarrage si des brouillons de commande sont en suspens
- Statut *Hors service* pour les plats annulés après validation

### Paramètres

- Accessible depuis l'interface principale à tout moment (plus uniquement au démarrage)
- Section *Impression* : activation/désactivation de l'imprimante, identification (Vendor ID, Product ID, profil), options d'impression automatique à la validation (ticket client et ticket cuisine configurables séparément)
- Configuration persistée dans `app_config.json`

### Impression thermique

- Découplée de la validation : les tickets peuvent être réimprimés manuellement depuis l'historique
- Impression automatique désormais configurable (activable/désactivable, par type de ticket)
- Configuration de l'imprimante chargée dynamiquement depuis `app_config.json` (plus de config statique en dur)

---

## Architecture et données

- Nouvelles métadonnées de commande : flag *Prioritaire*, champ *Contact*
- Nouveau dossier `/commandes/corrompu/` pour l'isolation des fichiers JSON invalides
- Cache stock en mémoire avec persistance différée (sauvegarde uniquement à la validation ou à l'annulation)
- Journalisation structurée JSON Lines (un fichier par jour dans `logs/`)
- Configuration applicative centralisée dans `app_config.json` (remplace `config_printer.py` statique)
- Démarrage sur la page Paramètres lors du premier lancement

---

## Déploiement cible

La V2.0.0 est conçue pour fonctionner sur un réseau local (LAN) composé de Raspberry Pi :

- **Poste principal** — saisie des commandes, fenêtre d'affichage client et centralisation des données sur le dossier partagé
- **Postes secondaires** (un ou plusieurs) — postes de préparation cuisine en affichage plein écran, accédant aux données via le dossier partagé

---

*Version précédente : 1.2.2 (17 juin 2025) — Interface Tkinter, MegaSouye 9*
