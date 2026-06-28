# Morphoz SnackApp — Patch Notes V2.5.0

---

## Rafraîchissement incrémental des affichages

Les modules de suivi (poste cuisine, panneau de suivi commandes, historique, journal, stock) ont été entièrement revus pour n'effectuer aucun travail inutile à chaque tick de timer :

- **Court-circuit par signature** : avant toute lecture de fichier, chaque module calcule une empreinte légère du dossier (horodatage + taille de chaque fichier JSON). Si rien n'a changé depuis le dernier rafraîchissement, l'affichage est conservé tel quel sans aucune lecture disque.
- **Cache de lecture JSON** : `charger_json` ne reparse le JSON d'un fichier que si son horodatage ou sa taille a changé depuis le dernier accès. Les fichiers non modifiés sont retournés depuis la mémoire.
- **Diff UI** : seules les cartes (commandes, plats, entrées de journal) effectivement modifiées sont reconstruites. L'état déplié des commandes dans le suivi est préservé entre les rafraîchissements.

Ces optimisations sont particulièrement sensibles sur les postes cuisine à ressources limitées (4 Go RAM) lisant les fichiers de commandes depuis un partage réseau LAN.

---

## Boutons filtre dynamiques sur le poste de préparation

Les boutons de filtre par type de plat du poste cuisine sont désormais chargés depuis la carte active plutôt qu'une liste statique :

- Les types disponibles reflètent la carte en service (les types archivés n'apparaissent pas sauf s'ils ont encore des plats en cours de préparation)
- Si un plat d'un type archivé est encore en préparation, un bouton filtre temporaire apparaît le temps de sa finalisation
- Les boutons sont stables entre les rafraîchissements (pas de reconstruction à chaque tick)

---

*Version précédente : 2.4.0 (25 juin 2026) — Boutons de retour de statut ; correction stocks grillades ; correction dossier data ; icônes SVG ; optimisation rafraîchissement widgets visibles*
