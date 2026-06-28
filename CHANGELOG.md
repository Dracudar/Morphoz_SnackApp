# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier, généré automatiquement à partir des commits de chaque version.

Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## [2.5.3] - 2026-06-28

### Corrigé
- **ci** : ajoute libcairo2-dev aux dépendances système Linux

### Documentation
- **architecture** : mise à jour pour la v2.5.3

### Maintenance
- **release** : passe en version 2.5.3


## [2.5.2] - 2026-06-28

### Corrigé
- **printer** : fallback sur _renderPM si rlPyCairo indisponible

### Divers
- doc: mis à jour pour le fix 2.5.2


## [2.5.1] - 2026-06-28

### Corrigé
- **printer** : ajout d'une dépendance manquante pour la convertion d'image svg vers png utilisée pour l'impression des tickets récap
- **suivi** : corrige les crashs removeWidget dans ConteneurSuiviCommande (ARM64/Qt 6.8.x)
- corrige les crashs de lancement sur ARM64/Raspberry Pi (Qt 6.8.x)

### Maintenance
- prépare la version 2.5.1


## [2.5.0] - 2026-06-28

### Ajouté
- **poste-preparation** : boutons filtre dynamiques + rafraîchissement incrémental

### Documentation
- prépare la documentation de la version 2.5.0
- **changelog** : ajoute l'entrée v2.4.0

### Tests
- **file_io** : cache mtime, signatures et élagage
- **data_sources** : signatures live/history/stock
- **suivi** : diff incrémental et préservation de l'état déplié


## [2.4.0] - 2026-06-25

### Ajouté
- **version** : incrémente APP_VERSION à 2.4.0
- **grillade** : accompagnements dynamiques depuis le stock
- **historique,prepa** : remplace les flèches textuelles par les icônes SVG directionnelles
- **icons** : ajout des icônes fléchées SVG (haut, bas, gauche, droite)
- **icones** : ajout de widget_icone_texte(nom, couleur, texte, taille_icone, *, taille_police, gras, espacement) dans icones.py — widget non-interactif icône SVG + libellé, analogue lecture seule de _bouton_item du volet de navigation
- **assets** : ajout de check.svg (coche) et hourglass.svg (sablier) dans assets/icons/
- **prepa** : bouton retour au statut En préparation depuis Prêt
- **prepa** : remplace l'emoji ⚡ du badge prioritaire par flash.svg
- **prepa** : remplace les emojis par des icônes SVG dans les boutons
- **historique** : zone d'action à largeur fixe avec boutons de retour de statut
- boutons de retour de statut avec icônes SVG (historique + poste prépa)
- **prepa** : retour arrière sur les statuts Prêt et Livré
- **ui/icones** : ajoute le paramètre rotation aux fonctions d'icônes SVG
- **icons** : ajout de trois nouveau icons pour remplacer des emojis
- **icons** : ajout des icônes check et hourglass en SVG

### Corrigé
- **test** : corrige la fixture logs_path après l'ajout du garde data_folder_est_configure dans log()
- **icons** : mise à jour de l'icône des paramètres avec un nouveau design SVG
- **stock** : invalide le cache de stock lors du changement de dossier de données
- **config** : champ dossier data vide par défaut, pas de création automatique
- **suivi_exterieur** : remplace les emojis par des icônes SVG dans les titres de section
- **suivi_exterieur** : titre "Prêts à récupérer" utilise check.svg via icone_coloree au lieu de l'emoji ✓
- **suivi_exterieur** : titre "En préparation" utilise hourglass.svg via icone_coloree au lieu de l'emoji ⏳
- **ci** : supprime les dépôts Microsoft avant apt-get update
- **stock** : correction du calcul des quantités pour les grillades en préparation
- **ui** : remplace le bouton hamburger par le logo MegaSnack cliquable
- **ui_prep** : remplace le bouton hamburger par le logo MegaSnack cliquable
- **suivi_exterieur** : remplace les symboles texte par des icônes SVG
- **ui_prep** : bascule les icônes de l'app préparation vers icones.py

### Modifié
- **icones** : extrait widget_icone_texte comme utilitaire général réutilisable
- **suivi_exterieur** : _build_titre devient un wrapper de mise à l'échelle qui délègue à widget_icone_texte
- **suivi_exterieur** : ajout de la méthode _build_titre pour créer un widget icône SVG + libellé mis à l'échelle
- **suivi_exterieur** : imports QSize et icone_coloree ajoutés
- **historique** : zone d'action en 3 colonnes fixes par statut
- **icon** : remplacement des icônes de pizza et salade composée

### Documentation
- prépare la documentation de la version 2.4.0

### Tests
- **app_config** : couverture des nouvelles fonctions et comportements V2.4.0

### Maintenance
- **suivi_exterieur** : suppression de l'import QSize et icone_coloree devenus inutiles dans ce module

### Divers
- perf(ui): ne rafraîchir les widgets que quand ils sont visibles
- Revert "feat: boutons de retour de statut avec icônes SVG (historique + poste prépa)"
- revert(ui): annule les modifications UI prématurées de carte_plat et conteneur_suivi_commande
- Refactor (icons): modifications de certains icônes du volet latérale


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
