#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stats.py - Agrégation des statistiques de vente

Description:
    Calcule le récapitulatif de vente à partir des commandes terminées de
    l'historique (src.backend.data_sources.get_all_history_orders) : totaux,
    ventilation par type de plat, par moyen de paiement, par recette de pizza,
    et chiffre d'affaires par jour.

    Seules les commandes au statut "terminée" sont comptabilisées (une
    commande en cours n'est pas encore une vente finalisée) ; au sein d'une
    commande terminée, les plats individuellement annulés sont exclus.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.05

Date de modification:
    2026.07.05
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional


def _order_datetime(order: Dict[str, Any]) -> Optional[datetime]:
    """Retourne le datetime de création de la commande (date seule si l'heure est absente)."""
    created = order.get("created_at", ["", ""])
    if not isinstance(created, list) or not created:
        return None
    date_str = str(created[0]).strip()
    if not date_str:
        return None
    time_str = str(created[1]).strip() if len(created) >= 2 else ""
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            d = datetime.strptime(date_str, fmt)
        except ValueError:
            continue
        if time_str:
            try:
                t = datetime.strptime(time_str, "%H:%M")
                return d.replace(hour=t.hour, minute=t.minute)
            except ValueError:
                pass
        return d
    return None


def _cle_tri_date(date_str: str) -> datetime:
    """Clé de tri chronologique pour une date au format JJ/MM/AAAA (ou JJ/MM/AA)."""
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.min


def calculer_statistiques(
    orders: List[Dict[str, Any]],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calcule le récapitulatif de vente sur les commandes terminées de la période donnée.

    :param orders: commandes issues de get_all_history_orders()
    :param date_from: borne de début incluse (None = pas de borne)
    :param date_to: borne de fin incluse (None = pas de borne)
    :return: dict avec les clés "totaux", "plats", "paiements", "recettes_pizza"
        et "ca_par_jour".
    """
    plats: Dict[str, Dict[str, float]] = defaultdict(lambda: {"quantite": 0, "montant": 0.0})
    paiements: Dict[str, Dict[str, float]] = defaultdict(lambda: {"quantite": 0, "montant": 0.0})
    recettes_pizza: Dict[str, int] = defaultdict(int)
    ca_par_jour: Dict[str, Dict[str, float]] = defaultdict(lambda: {"montant": 0.0, "quantite": 0})

    nb_commandes = 0
    montant_total = 0.0
    nb_plats = 0
    nb_pizzas = 0

    for order in orders:
        if (order.get("status") or "").lower() != "terminée":
            continue

        dt = _order_datetime(order)
        if date_from and (dt is None or dt < date_from):
            continue
        if date_to and (dt is None or dt > date_to):
            continue

        montant = order.get("amount") or 0
        nb_commandes += 1
        montant_total += montant

        created = order.get("created_at", ["", ""])
        jour = str(created[0]).strip() if created else ""
        jour = jour or "Inconnu"
        ca_par_jour[jour]["montant"] += montant
        ca_par_jour[jour]["quantite"] += 1

        type_paiement = order.get("payment_type") or "Inconnu"
        paiements[type_paiement]["quantite"] += 1
        paiements[type_paiement]["montant"] += montant

        for item in order.get("items", []):
            if (item.get("status") or "").lower() == "annulé":
                continue
            type_plat = item.get("plat") or item.get("nom") or "Inconnu"
            prix = item.get("price") or 0
            plats[type_plat]["quantite"] += 1
            plats[type_plat]["montant"] += prix
            nb_plats += 1

            if type_plat.lower() == "pizza":
                recette = str(item.get("recette") or "Inconnue").strip()
                if recette.endswith(" - Modifié !"):
                    recette = recette[: -len(" - Modifié !")]
                recettes_pizza[recette or "Inconnue"] += 1
                nb_pizzas += 1

    liste_plats = [
        {
            "nom": nom,
            "quantite": v["quantite"],
            "montant": round(v["montant"], 2),
            "prix_moyen": round(v["montant"] / v["quantite"], 2) if v["quantite"] else 0,
        }
        for nom, v in plats.items()
    ]
    liste_plats.sort(key=lambda p: p["quantite"], reverse=True)

    liste_paiements = [
        {
            "type": type_paiement,
            "quantite": v["quantite"],
            "montant": round(v["montant"], 2),
            "pourcentage": round(100 * v["quantite"] / nb_commandes, 1) if nb_commandes else 0,
        }
        for type_paiement, v in paiements.items()
    ]
    liste_paiements.sort(key=lambda p: p["quantite"], reverse=True)

    liste_recettes = [
        {
            "recette": recette,
            "quantite": qte,
            "pourcentage": round(100 * qte / nb_pizzas, 1) if nb_pizzas else 0,
        }
        for recette, qte in recettes_pizza.items()
    ]
    liste_recettes.sort(key=lambda r: r["quantite"], reverse=True)

    liste_ca_jour = [
        {"date": jour, "montant": round(v["montant"], 2), "quantite": v["quantite"]}
        for jour, v in ca_par_jour.items()
    ]
    liste_ca_jour.sort(key=lambda j: _cle_tri_date(j["date"]))

    return {
        "totaux": {
            "nb_commandes": nb_commandes,
            "montant_total": round(montant_total, 2),
            "nb_plats": nb_plats,
            "panier_moyen": round(montant_total / nb_commandes, 2) if nb_commandes else 0,
        },
        "plats": liste_plats,
        "paiements": liste_paiements,
        "recettes_pizza": liste_recettes,
        "ca_par_jour": liste_ca_jour,
    }
