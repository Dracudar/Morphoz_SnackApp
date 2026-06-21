# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier, généré automatiquement à partir des commits de chaque version.

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [2.3.0] - 2026-06-21

### Ajouté
- **ui** : centralise le rendu et la coloration des icônes SVG
- remplace les emojis du volet de navigation par des icônes SVG
- **icons** : ajout de nouveau icônes pour le volet latéral

### Corrigé
- **ui** : corrige le flou des grandes icônes dans src/UI/utils/icones.py
- **spec** : ajout de la collecte des fichiers dans src/utils pour PyInstaller

### Modifié
- **ui** : bascule tous les appels d'icônes vers src/UI/utils/icones.py

### Documentation
- **architecture** : documente src/UI/utils/icones.py dans la couche UI.

### Maintenance
- **release** : prépare la version 2.3.0
- **ui** : supprime les fonctions d'icônes devenues obsolètes


## [2.2.2] - 2026-06-20

### Corrigé
- **ci** : exécute les vérifications de version/doc dès la PR vers main
- **ci** : utilise ubuntu-22.04-arm pour le build aarch64

### Documentation
- **architecture** : confirme ARCHITECTURE.md à jour pour la v2.2.2
- ajoute l'entrée 2.2.2 au tableau Historique des versions du README

### Maintenance
- **release** : prépare la version 2.2.2


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
