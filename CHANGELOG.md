# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier, généré automatiquement à partir des commits de chaque version.

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [2.2.1] - 2026-06-20

### Ajouté
- **ci** : build PyInstaller natif aarch64 pour Raspberry Pi 5

### Divers
- Merge branch 'fix/ci-doc-linux-aarch64'


## [2.2.0] - 2026-06-19

### Ajouté
- bascule en version mineure 2.2.0 et renomme la convention PATCHNOTE_V
- **plats** : centralise les feuilles de style des dialogues de personnalisation
- échec bloquant si la version n'est pas incrémentée + CHANGELOG auto-généré
- **scripts** : ajoute generate_changelog.py qui extrait les lignes Conventional Commits depuis le dernier tag et génère une section CHANGELOG.md groupée par type (Ajouté/Corrigé/Documentation/...)
- ajoute la vérification automatique de la documentation avant tag/release

### Corrigé
- corrige le blocage de version 2.1.3 et complète la documentation
- **ui** : corrige le fond grisé qui persiste après fermeture du volet via la croix
- **requirements** : réorganise les dépendances pour l'impression de tickets
- journalise les exceptions silencieusement avalées
- sécurise les accès concurrents aux fichiers JSON partagés en LAN

### Documentation
- ajoute CHANGELOG.md à la racine, documente la nouvelle politique dans CLAUDE.md et met à jour l'arborescence du README
- **CLAUDE** : documente les exigences de vérification documentaire avant fusion vers main

### Tests
- ajoute la couverture manquante sur paiements et plats_router
