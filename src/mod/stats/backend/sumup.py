#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sumup.py - Rapprochement des paiements carte avec le relevé CSV SumUp

Description:
    Lit le relevé de ventes CSV exporté depuis SumUp (une ligne par article vendu,
    éventuellement regroupable par référence de transaction) et le rapproche des
    commandes de l'application payées par carte, afin de repérer les erreurs de
    saisie du moyen de paiement : paiement marqué "Carte" sur l'app mais absent du
    relevé, ou inversement transaction présente sur le relevé sans commande
    correspondante.

    Le relevé SumUp couvre plusieurs TPE : le rapprochement se limite au "Compte"
    (vendeur) choisi par l'utilisateur, qui identifie le TPE du snack. Le
    regroupement par référence de transaction fonctionne aussi bien sur un export
    "une ligne = un article" que "une ligne = une transaction" (le regroupement
    redevient alors une opération identité).

    La comparaison associe une commande à une transaction quand leur montant est
    identique et que leur date/heure ne s'écarte pas de plus de la tolérance
    donnée — cette tolérance est nécessaire car la validation du paiement sur
    l'app est manuelle (elle survient donc quelques instants après le paiement
    réel au TPE).

Author :
    Dracudar

Version:
    1.1

Date de création :
    2026.07.13

Date de modification:
    2026.07.14
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any, Dict, List, Optional

_FORMATS_DATE = (
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
)

_MOIS_FR = {
    "janv": 1, "févr": 2, "fevr": 2, "mars": 3, "avr": 4, "mai": 5, "juin": 6,
    "juil": 7, "août": 8, "aout": 8, "sept": 9, "oct": 10, "nov": 11, "déc": 12, "dec": 12,
}


def _corriger_encodage(texte: str) -> str:
    """Corrige un mojibake UTF-8 ré-encodé en Latin-1 (ex. "RÃ©f." -> "Réf."), tel
    que produit par certains exports SumUp."""
    if "Ã" not in texte and "Â" not in texte:
        return texte
    try:
        return texte.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return texte


def lire_lignes_csv(chemin_fichier: str) -> List[Dict[str, str]]:
    """Lit le CSV d'export SumUp et retourne les lignes sous forme de dictionnaires
    en-tête -> valeur, en corrigeant l'encodage si nécessaire.

    :param chemin_fichier: chemin vers le fichier CSV exporté depuis SumUp.
    :return: liste des lignes du relevé.
    """
    with open(chemin_fichier, "rb") as f:
        donnees_brutes = f.read()

    texte = _corriger_encodage(donnees_brutes.decode("utf-8-sig", errors="replace"))

    lecteur = csv.DictReader(io.StringIO(texte), delimiter=",")
    return [
        {(cle or "").strip(): (valeur or "").strip() for cle, valeur in ligne.items() if cle}
        for ligne in lecteur
    ]


def comptes_disponibles(lignes: List[Dict[str, str]]) -> List[str]:
    """Retourne la liste triée des valeurs distinctes de la colonne "Compte" (un
    compte par TPE)."""
    return sorted({ligne.get("Compte", "") for ligne in lignes if ligne.get("Compte", "").strip()})


def _parser_montant(valeur: str) -> float:
    """Convertit un montant textuel ("12.50", "12,50" ou "1.234,56") en float."""
    texte = (valeur or "").strip().replace("\xa0", "").replace(" ", "")
    if not texte:
        return 0.0
    if "," in texte and "." in texte:
        texte = texte.replace(".", "").replace(",", ".")
    elif "," in texte:
        texte = texte.replace(",", ".")
    try:
        return float(texte)
    except ValueError:
        return 0.0


def _parser_date_sumup_fr(texte: str) -> Optional[datetime]:
    """Parse une date au format textuel français de SumUp ("3 juil. 2026 19:42"),
    le mois en toutes lettres n'étant pas exploitable par strptime sans dépendre
    de la locale système."""
    morceaux = texte.split()
    if len(morceaux) != 4:
        return None
    jour_str, mois_str, annee_str, heure_str = morceaux
    mois = _MOIS_FR.get(mois_str.rstrip(".").lower())
    if mois is None:
        return None
    heure_morceaux = heure_str.split(":")
    if len(heure_morceaux) not in (2, 3):
        return None
    try:
        jour = int(jour_str)
        annee = int(annee_str)
        heure = int(heure_morceaux[0])
        minute = int(heure_morceaux[1])
        seconde = int(heure_morceaux[2]) if len(heure_morceaux) == 3 else 0
        return datetime(annee, mois, jour, heure, minute, seconde)
    except ValueError:
        return None


def _parser_date_sumup(valeur: str) -> Optional[datetime]:
    """Parse une date/heure de relevé SumUp en essayant les formats courants, puis
    le format textuel français ("3 juil. 2026 19:42")."""
    texte = (valeur or "").strip()
    if not texte:
        return None
    for fmt in _FORMATS_DATE:
        try:
            return datetime.strptime(texte, fmt)
        except ValueError:
            continue
    return _parser_date_sumup_fr(texte)


def horodatage_commande(valeur: Any) -> Optional[datetime]:
    """Convertit un champ ["JJ/MM/AAAA", "HH:MM"] (format des commandes de l'app,
    ex. "validation_at") en datetime, ou None si vide/invalide."""
    if not isinstance(valeur, list) or len(valeur) < 2:
        return None
    date_str, heure_str = str(valeur[0]).strip(), str(valeur[1]).strip()
    if not date_str or not heure_str:
        return None
    for fmt_date in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            d = datetime.strptime(date_str, fmt_date)
        except ValueError:
            continue
        try:
            t = datetime.strptime(heure_str, "%H:%M")
        except ValueError:
            return None
        return d.replace(hour=t.hour, minute=t.minute)
    return None


def grouper_transactions(lignes: List[Dict[str, str]], compte: str) -> List[Dict[str, Any]]:
    """Filtre les lignes du relevé sur le compte donné et les regroupe par référence
    de transaction (une transaction TPE peut être exportée sur plusieurs lignes, une
    par article vendu) : le montant TTC total de chaque transaction est la somme des
    lignes du groupe.

    :param lignes: lignes issues de lire_lignes_csv().
    :param compte: valeur de la colonne "Compte" à isoler.
    :return: liste de transactions {reference, datetime, montant, moyen_paiement,
        lisible}, triée par date/heure. "lisible" est False si la date n'a pas pu
        être interprétée (la transaction est alors exclue du rapprochement mais
        listée pour information).
    """
    groupes: Dict[str, Dict[str, Any]] = {}
    for i, ligne in enumerate(lignes):
        if ligne.get("Compte", "") != compte:
            continue
        reference = ligne.get("Réf. transaction", "").strip() or f"(ligne {i + 1})"
        dt = _parser_date_sumup(ligne.get("Date", ""))
        montant = _parser_montant(ligne.get("Prix (TTC)", ""))

        groupe = groupes.setdefault(reference, {
            "reference": reference,
            "datetime": dt,
            "montant": 0.0,
            "moyen_paiement": ligne.get("Moyen de paiement", ""),
            "lisible": dt is not None,
        })
        groupe["montant"] += montant
        if groupe["datetime"] is None and dt is not None:
            groupe["datetime"] = dt
            groupe["lisible"] = True

    transactions = list(groupes.values())
    for transaction in transactions:
        transaction["montant"] = round(transaction["montant"], 2)
    transactions.sort(key=lambda t: t["datetime"] or datetime.min)
    return transactions


def rapprocher_paiements_carte(
    commandes_carte: List[Dict[str, Any]],
    transactions_sumup: List[Dict[str, Any]],
    tolerance_minutes: float = 5,
) -> Dict[str, Any]:
    """Rapproche les commandes payées par carte avec les transactions SumUp, par
    correspondance montant identique + écart de date/heure sous la tolérance donnée.

    Algorithme glouton : associe en priorité les paires (commande, transaction) à
    montant identique dont l'écart de date/heure est le plus faible, jusqu'à
    épuisement des candidats possibles — chaque commande et chaque transaction ne
    peut être utilisée que dans une seule paire.

    :param commandes_carte: liste de {id, datetime, montant} — commandes de l'app
        payées par carte.
    :param transactions_sumup: transactions issues de grouper_transactions().
    :param tolerance_minutes: écart de date/heure maximal toléré pour un rapprochement.
    :return: dict avec "paires" (rapprochements réussis), "commandes_sans_correspondance"
        (carte sur l'app, absentes du relevé SumUp) et "transactions_sans_correspondance"
        (présentes sur le relevé SumUp, absentes de l'app).
    """
    candidats = []
    for i, commande in enumerate(commandes_carte):
        if commande.get("datetime") is None:
            continue
        for j, transaction in enumerate(transactions_sumup):
            if not transaction.get("lisible"):
                continue
            if abs(commande["montant"] - transaction["montant"]) > 0.01:
                continue
            ecart_minutes = abs((commande["datetime"] - transaction["datetime"]).total_seconds()) / 60
            if ecart_minutes > tolerance_minutes:
                continue
            candidats.append((ecart_minutes, i, j))

    candidats.sort(key=lambda c: c[0])
    commandes_associees: set = set()
    transactions_associees: set = set()
    paires = []
    for ecart_minutes, i, j in candidats:
        if i in commandes_associees or j in transactions_associees:
            continue
        commandes_associees.add(i)
        transactions_associees.add(j)
        paires.append({
            "commande": commandes_carte[i],
            "transaction": transactions_sumup[j],
            "ecart_minutes": round(ecart_minutes, 1),
        })

    commandes_sans_correspondance = [
        c for idx, c in enumerate(commandes_carte) if idx not in commandes_associees
    ]
    transactions_sans_correspondance = [
        t for idx, t in enumerate(transactions_sumup) if idx not in transactions_associees
    ]

    return {
        "paires": paires,
        "commandes_sans_correspondance": commandes_sans_correspondance,
        "transactions_sans_correspondance": transactions_sans_correspondance,
    }


def suggerer_commandes_probables(
    transactions_sans_correspondance: List[Dict[str, Any]],
    commandes_candidates: List[Dict[str, Any]],
    tolerance_minutes: float = 5,
) -> Dict[str, List[Dict[str, Any]]]:
    """Pour chaque transaction SumUp restée sans commande carte correspondante, recherche
    parmi TOUTES les commandes non déjà rapprochées (quel que soit leur moyen de paiement)
    celles dont le montant est identique et la date/heure de validation proche : indice
    probable d'une erreur de saisie du moyen de paiement sur l'app (ex. "Espèces" au lieu
    de "Carte"), pour éviter de rouvrir chaque commande à la main.

    :param transactions_sans_correspondance: transactions issues de
        rapprocher_paiements_carte()["transactions_sans_correspondance"].
    :param commandes_candidates: commandes {id, datetime, montant, payment_type} à passer
        au crible, typiquement toutes les commandes de la période à l'exclusion de celles
        déjà rapprochées.
    :param tolerance_minutes: écart de date/heure maximal toléré.
    :return: dict référence de transaction -> liste de commandes candidates (avec
        "ecart_minutes" ajouté), triée par écart croissant.
    """
    suggestions: Dict[str, List[Dict[str, Any]]] = {}
    for transaction in transactions_sans_correspondance:
        if not transaction.get("lisible"):
            suggestions[transaction["reference"]] = []
            continue

        candidats = []
        for commande in commandes_candidates:
            if commande.get("datetime") is None:
                continue
            if abs(commande["montant"] - transaction["montant"]) > 0.01:
                continue
            ecart_minutes = abs((commande["datetime"] - transaction["datetime"]).total_seconds()) / 60
            if ecart_minutes > tolerance_minutes:
                continue
            candidats.append({**commande, "ecart_minutes": round(ecart_minutes, 1)})

        candidats.sort(key=lambda c: c["ecart_minutes"])
        suggestions[transaction["reference"]] = candidats

    return suggestions
