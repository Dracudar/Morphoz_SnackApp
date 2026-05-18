# Morphoz_SnackApp

Application de gestion de snack pour événements (ex : MégaSouye), développée pour l'association Morphoz.

## Fonctionnalités principales

- **Prise de commande** (pizzas, grillades, frites, fish & chips, salades composées, etc.)
- **Personnalisation des plats** (choix des ingrédients, accompagnements, etc.)
- **Gestion des stocks** (mise à jour automatique selon les commandes)
- **Suivi des commandes** (statuts : en attente, en préparation, prêt, livré)
- **Gestion des paiements** (CB, espèces, repas gratuits)
- **Impression de tickets** (pour chaque plat et pour la commande globale)
- **Archivage automatique** des commandes terminées

## Utilisation

Au lancement, l'application propose de sélectionner les fichiers de stock et de menu, puis permet la prise de commandes, la personnalisation des plats, la validation et le suivi en temps réel.

Les tickets sont imprimés automatiquement à chaque validation de commande.

## Développement & maintenance
### Installation

1. **Cloner le dépôt**  
   ```bash
   git clone https://github.com/Dracudar/Morphoz_SnackApp
   cd Morphoz_SnackApp
   ```

2. **Installer les dépendances**  
   Utilisation de Python 3.14.5 ou suppérieur recommandé.

   Créer un environement virtuel pour travailler dans de bonnes condition :
   ```bash
   cd <chemin_du_projet>
   python -m venv .venv
   ```
   Activer l'environnement virtuelle créé :
   ```bash
   .\.venv\Scripts\activate
   ```
   Installer les dépendances dans l'environnement vituel du projet.
   ```bash
   pip install -r requirements.txt
   ```
   
   Liste des dépendances :
   - **PySide6** : Question de l'interface Qt

3. **Lancer l'application**  
   Il est possible de lancer l'interface sans compiler avec la commande suivante : 
   ```bash
   python -m src.core.app
   ```

### Structure détaillée du projet

```
Morphoz_SnackApp/
│
├── asset/
│
├── src/
│   ├── core/
│   │   └── app.py
│   │
│   ├── UI/
│   │   ├── widget/
│   │   |   ├── init_view.py            # Vue d'initialisation (sélection fichiers, etc.)
│   │   |   └── main_view.py            # Vue principale (prise et suivi des commandes)
│   │   └── main_window.py
│   │
│   ├── backend/
│   │   ├── chemins_exploitation.py     # Chargement des fichiers JSON, initialisation des dossiers
│   │   ├── chemins_gestion.py          # Gestion et sauvegarde des chemins de fichiers
│   │   ├── commandes_saisie_save.py    # Création/mise à jour des fichiers de commande
│   │   ├── commandes_saisie_gestion.py # Validation, annulation, gestion des statuts de commande
│   │   ├── commandes_suivi_gestion.py  # Changement de statut des plats (prêt, livré, terminé)
│   │   ├── commandes_utils.py          # Utilitaires : génération d'ID, chargement JSON sécurisé
│   │   └── printer.py                  # Impression des tickets (plats et commandes)
│   │
│   └── utils/                          # (optionnel) Fonctions utilitaires partagées
│
├── requirements.txt                    # Dépendances Python du projet
├── README.md                           # Documentation du projet
└── .gitignore                          # Fichiers à ignorer par git
```

## Développement

- **Ajouter une fonctionnalité** : Créer un module dans `src/frontend/temp/` ou `src/backend/` selon le besoin.
- **Tests** : Ajouter vos tests dans le dossier `tests/` et lancer avec `pytest`.

## Auteurs

- Dracudar

## Licence

Projet open-source sous licence MIT.

## Historique version

<table>
  <tr>
    <th>Version</th>
    <th>Date de sortie</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>2.2.0</td>
    <td>17/06/2025</td>
    <td>Première version de production</td>
  </tr>
  <tr>
    <td>3.0.0</td>
    <td></td>
    <td>Première version Qt</td>
  </tr>
</table>

---

*Pour toute question ou contribution, contactez l'équipe Morphoz !*