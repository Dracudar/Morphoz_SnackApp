# Morphoz SnackApp — Patch Notes V2.4.0

---

## Boutons de retour de statut

Il est désormais possible de corriger une erreur de statut depuis la cuisine et l'historique, sans avoir à annuler le plat :

- **Prêt → En préparation** : un plat marqué « Prêt » par erreur peut être remis « En préparation » depuis le poste cuisine et depuis le panneau de suivi
- **Livré → Prêt** : un plat marqué « Livré » par erreur peut être remis « Prêt » depuis l'historique et depuis le panneau de suivi
- Si la commande était déjà passée à l'état « Terminée », elle est automatiquement rouverte et remise dans les commandes en cours

---

## Correction du calcul des stocks pour les grillades

Le calcul des quantités de viande réservées pour les grillades en cours de préparation était incorrect. Les quantités affichées correspondent maintenant exactement à ce qui a été commandé.

---

## Correction de la gestion du dossier de données

- Le champ « Dossier de données » dans les Paramètres est désormais vide par défaut : aucun chemin n'est pré-rempli automatiquement
- La structure de dossiers n'est plus créée au démarrage si aucun dossier n'a été configuré explicitement
- Quand le dossier de données change dans les Paramètres, le cache de stock est correctement invalidé : les quantités rechargées depuis le nouveau dossier sont exactes

---

## Icônes SVG dans l'affichage extérieur et le poste cuisine

Les emojis (susceptibles de s'afficher comme des cases vides selon le système) ont été remplacés par des icônes SVG dans la fenêtre d'affichage extérieur client et dans le poste de préparation cuisine.

---

## Optimisation du rafraîchissement de l'interface

Les modules en arrière-plan (non visibles) ne rechargent plus leurs données en tâche de fond. Le rafraîchissement ne s'effectue qu'au moment où un widget devient visible, ce qui réduit les lectures disque inutiles sur les machines moins puissantes.

---

*Version précédente : 2.3.0 (22 juin 2026) — Correction des dialogues de personnalisation ; icônes SVG dans le volet de navigation*
