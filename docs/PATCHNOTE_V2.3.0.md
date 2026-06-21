# Morphoz SnackApp — Patch Notes V2.3.0

---

## Correction des dialogues de personnalisation des plats

Dans la version compilée (PyInstaller), les dialogues de personnalisation (pizza, grillade, salade composée, crêpe) ne s'ouvraient plus — un module interne nécessaire à leur affichage n'était pas inclus dans l'exécutable. C'est corrigé.

---

## Nouvelles icônes du volet de navigation

Le volet de navigation latéral affiche désormais de vraies icônes (au lieu d'emojis, qui pouvaient s'afficher comme des cases vides selon les polices installées sur la machine) :

- Icônes blanches pour la navigation, rouge pour "Quitter"
- Tailles et centrage cohérents entre toutes les icônes, quel que soit le fichier source

---

*Version précédente : 2.2.2 (20 juin 2026) — Correction du build `aarch64` pour Raspberry Pi 5*
