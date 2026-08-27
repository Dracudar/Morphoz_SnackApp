# Politique de sécurité

## Portée du projet

Morphoz_SnackApp est actuellement une application de bureau (PySide6) qui ne repose
que sur des fichiers JSON locaux : aucune base de données, aucune API REST, aucun
service réseau écouté par l'application elle-même. Le seul usage réseau existant est
le partage du dossier `data/` sur un LAN (accès concurrent aux fichiers JSON via
`filelock`), pas un protocole exposé par l'application.

Une évolution vers une base de données (hébergement local ou sur un Raspberry Pi
distant dédié à l'événement) est envisagée pour une prochaine version majeure. Le cas
échéant, cette politique sera mise à jour pour couvrir la surface exposée par ce
service (authentification, port réseau, etc.). Si un tiers déploie sa propre instance
(Raspberry Pi ou autre) à partir de ce dépôt, la sécurisation de son déploiement
(réseau, accès physique, mises à jour) reste sous sa responsabilité — ce document ne
couvre que le code publié dans ce dépôt.

## Versions supportées

Le projet n'a pas de politique de maintenance à long terme (LTS) : seule la dernière
version stable publiée (tag `VX.Y.Z` sur `main`) reçoit des correctifs de sécurité.

| Version           | Support           |
| ------------------ | ------------------ |
| Dernière `VX.Y.Z`  | :white_check_mark: |
| Versions antérieures | :x:               |

## Signaler une vulnérabilité

Merci de **ne pas** ouvrir d'issue publique pour une faille de sécurité.

Deux options, par ordre de préférence :

1. **GitHub Security Advisories** (recommandé) : onglet [Security > Advisories](https://github.com/Dracudar/Morphoz_SnackApp/security/advisories/new) de ce dépôt, qui permet un échange privé avec le mainteneur.
2. **Email** : dracudar@gmail.com, avec autant de détails que possible (version concernée, étapes de reproduction, impact).

### Ce qu'il est utile de fournir

- Version de l'application (`APP_VERSION` dans `src/core/version.py`) et OS.
- Étapes de reproduction ou preuve de concept.
- Impact estimé (accès aux données, exécution de code, déni de service, etc.).

Le projet est maintenu par une seule personne sur son temps libre, de façon
bénévole : il n'y a pas de délai de réponse garanti.
