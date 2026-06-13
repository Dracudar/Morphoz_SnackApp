# Morphoz SnackApp — Patch Notes V1.2.2

*Date de sortie : 17 juin 2025*

---

## Première version de production

La V1.2.2 est la première version stabilisée de l'application, basée sur **Tkinter**. Elle constitue la référence de production pour l'événement MegaSouye 9.

---

## Gestion des commandes

- Saisie des commandes par plat avec statuts : *En attente → En préparation → Prêt → Livré*
- Panneau de suivi des commandes (boutons *Prêt* / *Livrer*) intégré à l'interface principale
- Annulation groupée de tous les plats d'une commande
- Suivi du type de plat (Pizza, Grillade, Frites…)

---

## Personnalisation des plats

- Pizza : choix de la recette puis personnalisation des ingrédients (sauce de base, ajout/retrait), champ recette imprimé si modifié
- Grillade : choix des viandes (2 portions max) et de l'accompagnement
- Salade composée : sélection des ingrédients par catégorie
- Ajout direct (sans popup) pour les frites, le fish & chips et la pizza dessert

---

## Paiement

- Support multi-mode : CB (SumUp), espèces, repas offert (artistes / bénévoles)
- Gestion des quantités de repas offerts

---

## Impression thermique (Epson TM-T20)

- Ticket cuisine imprimé automatiquement à la validation de chaque plat
- Ticket récapitulatif client
- En-tête personnalisé avec logo du snack
- Gestion des erreurs de connexion à l'imprimante

---

## Gestion du stock

- Écran de stock à onglets (Plats / Accompagnement / Ingrédients) avec bascule de l'état *rupture* par article
- Cache mémoire `StockCache` pour le suivi en temps réel
- Décrémentation automatique à la validation des commandes
- Vérification de disponibilité avant prise de commande

---

## Interface & assets

- Amélioration visuelle des listes de plats et des scrollbars
- Icônes dédiées : pizza, grillade, frites, poisson, salade, repas offert, paramètres, retour, annulation…
- Logo snack (MS9) et images d'en-tête pour les tickets

---

## Configuration & données

- Menus au format JSON (`carte_MS09.json`)
- Dépendances : `Pillow`, `python-escpos`, `pyusb`
- `.env` et dossier `proto/` exclus du dépôt
