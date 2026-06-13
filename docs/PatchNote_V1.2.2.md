# Morphoz SnackApp — Patch Notes V1.2.2

*Date de sortie : 17 juin 2025*

---

## Première version de production

La V1.2.2 est la première version stabilisée de l'application, basée sur **Tkinter**. Elle constitue la référence de production pour l'événement MegaSouye 9.

---

## Gestion des commandes

- Saisie des commandes par plat avec statuts : *En attente → En préparation → Prêt → Livré*
- Annulation groupée de tous les plats d'une commande
- Personnalisation des pizzas avec champ recette (imprimé si modifié)
- Suivi du type de plat (Pizza, Grillade, Frites…)

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

## Gestion du stock (cache)

- Classe `StockCache` pour le suivi en temps réel
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
