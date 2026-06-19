# Morphoz SnackApp — Patch Notes V2.2.0

---

## Fiabilité des données partagées en réseau local

Plusieurs postes (caisse, cuisine, suivi…) peuvent désormais lire et écrire les mêmes fichiers (stock, commandes, IDs journaliers) sur le réseau LAN sans risque de corruption :

- **Écriture atomique** : un fichier JSON n'est jamais laissé à moitié écrit en cas de coupure réseau ou de plantage en plein milieu d'une sauvegarde
- **Verrouillage inter-postes** : deux postes ne peuvent plus modifier le même fichier en même temps et s'écraser mutuellement leurs changements

---

## Correction d'affichage

- Le fond grisé du volet de navigation ne reste plus affiché après sa fermeture via la croix

---

## Fiabilisation du pipeline de release

- La documentation (README, `ARCHITECTURE.md`, patch note) est désormais vérifiée automatiquement avant la création de chaque tag/release
- Le `CHANGELOG.md` est généré automatiquement à partir des commits depuis la dernière version

---

*Version précédente : 2.1.2 (18 juin 2026) — Corrections de compilation PyInstaller*
