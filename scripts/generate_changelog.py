#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_changelog.py - Génère la section CHANGELOG.md d'une nouvelle version

Description:
    Parcourt les commits depuis le tag précédent, extrait les lignes au format
    Conventional Commits (`type(scope): description`, y compris les listes à
    puces dans le corps des commits), les regroupe par type et insère une
    nouvelle section en tête de CHANGELOG.md. Utilisé par le job `changelog`
    de auto-tag.yml avant la création du tag de version.

Author :
    Dracudar

Date de création :
    2026.06.19
"""

import argparse
import re
import subprocess
import sys

CATEGORIES = {
    "feat": "Ajouté",
    "fix": "Corrigé",
    "docs": "Documentation",
    "style": "Style",
    "refactor": "Modifié",
    "test": "Tests",
    "chore": "Maintenance",
}

# Ordre d'affichage des catégories dans le CHANGELOG
ORDRE_CATEGORIES = ["feat", "fix", "refactor", "docs", "style", "test", "chore"]

LIGNE_CONVENTIONAL = re.compile(
    r"^[-*]?\s*(feat|fix|docs|style|refactor|test|chore)(\(([^)]+)\))?!?:\s*(.+)$"
)

EN_TETE_FICHIER = (
    "# Changelog\n\n"
    "Toutes les modifications notables de ce projet sont documentées dans ce "
    "fichier, généré automatiquement à partir des commits de chaque version.\n\n"
    "Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).\n"
)


def lire_corps_commits(plage):
    """Retourne la liste des corps complets de commits (hors merges) sur la plage donnée."""
    separateur = "\x1e"
    resultat = subprocess.run(
        ["git", "log", plage, "--no-merges", f"--pretty=format:%B{separateur}"],
        capture_output=True,
        text=True,
        check=True,
    )
    corps = resultat.stdout.split(separateur)
    return [c.strip() for c in corps if c.strip()]


def extraire_entrees(corps_commits):
    """Extrait les entrées (type, scope, description) de toutes les lignes Conventional Commits."""
    entrees = {cle: [] for cle in CATEGORIES}
    lignes_brutes = []

    for corps in corps_commits:
        une_entree_trouvee = False
        for ligne in corps.splitlines():
            ligne = ligne.strip()
            if not ligne:
                continue
            match = LIGNE_CONVENTIONAL.match(ligne)
            if match:
                type_commit, _, scope, description = match.groups()
                entrees[type_commit].append((scope, description.strip()))
                une_entree_trouvee = True

        if not une_entree_trouvee:
            premiere_ligne = corps.splitlines()[0].strip()
            if premiere_ligne:
                lignes_brutes.append(premiere_ligne)

    return entrees, lignes_brutes


def formater_section(version, date, entrees, lignes_brutes):
    """Construit le texte Markdown de la nouvelle section de version."""
    lignes = [f"## [{version}] - {date}", ""]

    for type_commit in ORDRE_CATEGORIES:
        elements = entrees.get(type_commit, [])
        if not elements:
            continue
        lignes.append(f"### {CATEGORIES[type_commit]}")
        vus = set()
        for scope, description in elements:
            texte = f"**{scope}** : {description}" if scope else description
            if texte not in vus:
                vus.add(texte)
                lignes.append(f"- {texte}")
        lignes.append("")

    if lignes_brutes:
        lignes.append("### Divers")
        for ligne in dict.fromkeys(lignes_brutes):
            lignes.append(f"- {ligne}")
        lignes.append("")

    if len(lignes) == 2:
        lignes.append("- Aucun changement notable.")
        lignes.append("")

    return "\n".join(lignes)


def inserer_section(chemin_fichier, section):
    """Insère la nouvelle section juste après l'en-tête, avant les sections de version existantes."""
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            contenu = f.read()
    except FileNotFoundError:
        contenu = EN_TETE_FICHIER

    if not contenu.startswith("# Changelog"):
        contenu = EN_TETE_FICHIER + "\n" + contenu

    match_premiere_version = re.search(r"\n## \[", contenu)
    if match_premiere_version:
        position = match_premiere_version.start() + 1
        nouveau_contenu = contenu[:position] + section + "\n\n" + contenu[position:]
    else:
        nouveau_contenu = contenu.rstrip() + "\n\n" + section + "\n"

    with open(chemin_fichier, "w", encoding="utf-8") as f:
        f.write(nouveau_contenu.rstrip() + "\n")


def main():
    analyseur = argparse.ArgumentParser()
    analyseur.add_argument("--previous", default="", help="Tag précédent (vide si premier release)")
    analyseur.add_argument("--version", required=True, help="Nouvelle version (ex: 2.1.3)")
    analyseur.add_argument("--date", required=True, help="Date de sortie (YYYY-MM-DD)")
    analyseur.add_argument("--fichier", default="CHANGELOG.md")
    args = analyseur.parse_args()

    plage = f"{args.previous}..HEAD" if args.previous else "HEAD"
    corps_commits = lire_corps_commits(plage)
    entrees, lignes_brutes = extraire_entrees(corps_commits)
    section = formater_section(args.version, args.date, entrees, lignes_brutes)
    inserer_section(args.fichier, section)
    print(f"Section ajoutée pour la version {args.version} dans {args.fichier}.")


if __name__ == "__main__":
    sys.exit(main())
