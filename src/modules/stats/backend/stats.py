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

    Fournit également des statistiques opérationnelles calculées sur toutes
    les commandes validées (terminées, annulées ou encore en cours), car une
    commande annulée a bien été validée et compte donc dans l'affluence :
    - calculer_affluence : répartition horaire des validations de commande.
    - calculer_temps_preparation : durée entre validation de la commande et
      mise à disposition ("Prêt") de chaque plat, par type de plat.
    - calculer_delais_retrait : durée entre la mise à disposition d'un plat
      ("Prêt") et sa remise au client ("Livré"), par type de plat.

Author :
    Dracudar

Version:
    1.2

Date de création :
    2026.07.05

Date de modification:
    2026.07.08
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional


def _horodatage(valeur: Any) -> Optional[datetime]:
    """Convertit un champ ["JJ/MM/AAAA", "HH:MM"] (ou variante) en datetime, ou None si vide/invalide."""
    if not isinstance(valeur, list) or not valeur:
        return None
    date_str = str(valeur[0]).strip()
    if not date_str:
        return None
    time_str = str(valeur[1]).strip() if len(valeur) >= 2 else ""
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


def _order_datetime(order: Dict[str, Any]) -> Optional[datetime]:
    """Retourne le datetime de création de la commande (date seule si l'heure est absente)."""
    return _horodatage(order.get("created_at", ["", ""]))


def _dans_periode(dt: Optional[datetime], date_from: Optional[datetime], date_to: Optional[datetime]) -> bool:
    """Vérifie qu'un datetime tombe dans la période [date_from, date_to] (bornes incluses, None = pas de borne)."""
    if date_from and (dt is None or dt < date_from):
        return False
    if date_to and (dt is None or dt > date_to):
        return False
    return True


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
        if not _dans_periode(dt, date_from, date_to):
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


def calculer_composition_par_plat(
    orders: List[Dict[str, Any]],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Dict[str, Dict[str, Any]]:
    """Ventile la composition des plats vendus (commandes terminées) par type de plat.

    Exploite le champ "composition" des items, propre à chaque type de plat
    personnalisable : viandes/accompagnement (Grillade), garniture (Crêpe),
    ingrédients (Salade composée), ajouts/retraits (Pizza). Les plats simples
    (Frites, boissons, desserts...) n'ont pas de composition à ventiler et
    n'apparaissent donc pas dans le résultat.

    :param orders: commandes issues de get_all_history_orders()
    :param date_from: borne de début incluse sur la date de création (None = pas de borne)
    :param date_to: borne de fin incluse sur la date de création (None = pas de borne)
    :return: dict indexé par nom de plat, contenant des listes triées
        {nom, quantite} par sous-catégorie (ex. "viandes", "accompagnements").
    """
    viandes_grillade: Dict[str, float] = defaultdict(float)
    accompagnements_grillade: Dict[str, int] = defaultdict(int)
    garnitures_crepe: Dict[str, int] = defaultdict(int)
    ingredients_salade: Dict[str, int] = defaultdict(int)
    ajouts_pizza: Dict[str, int] = defaultdict(int)
    retraits_pizza: Dict[str, int] = defaultdict(int)

    for order in orders:
        if (order.get("status") or "").lower() != "terminée":
            continue

        dt = _order_datetime(order)
        if not _dans_periode(dt, date_from, date_to):
            continue

        for item in order.get("items", []):
            if (item.get("status") or "").lower() == "annulé":
                continue
            type_plat = item.get("plat") or item.get("nom") or "Inconnu"
            composition = item.get("composition")
            if not isinstance(composition, dict):
                continue

            if type_plat == "Grillade":
                for viande, quantite in (composition.get("Viandes") or {}).items():
                    viandes_grillade[viande] += quantite or 0
                accompagnement = composition.get("Accompagnement")
                if accompagnement and accompagnement != "Sans":
                    accompagnements_grillade[accompagnement] += 1
            elif type_plat == "Crêpe":
                for garniture in composition.get("Garniture") or []:
                    garnitures_crepe[garniture] += 1
            elif type_plat == "Salade composée":
                for ingredient in composition.get("Ingrédients") or []:
                    ingredients_salade[ingredient] += 1
            elif type_plat == "Pizza":
                for ingredient in composition.get("Ajouts") or []:
                    ajouts_pizza[ingredient] += 1
                for ingredient in composition.get("Retraits") or []:
                    retraits_pizza[ingredient] += 1

    def _classement(compteur: Dict[str, float]) -> List[Dict[str, Any]]:
        liste = [{"nom": nom, "quantite": quantite} for nom, quantite in compteur.items()]
        liste.sort(key=lambda x: x["quantite"], reverse=True)
        return liste

    resultat: Dict[str, Dict[str, Any]] = {}
    if viandes_grillade or accompagnements_grillade:
        resultat["Grillade"] = {
            "viandes": _classement(viandes_grillade),
            "accompagnements": _classement(accompagnements_grillade),
        }
    if garnitures_crepe:
        resultat["Crêpe"] = {"garnitures": _classement(garnitures_crepe)}
    if ingredients_salade:
        resultat["Salade composée"] = {"ingredients": _classement(ingredients_salade)}
    if ajouts_pizza or retraits_pizza:
        resultat["Pizza"] = {
            "ajouts": _classement(ajouts_pizza),
            "retraits": _classement(retraits_pizza),
        }

    return resultat


def calculer_affluence(
    orders: List[Dict[str, Any]],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calcule la répartition horaire des validations de commande (horaires d'affluence).

    Une commande compte dès qu'elle a été validée (passage en "en_cours"), quel que
    soit son statut final : une commande annulée a bien généré de l'affluence au
    moment de sa validation, même si elle n'a pas été facturée. Le filtrage de
    période se fait sur la date de validation, pas sur la date de création.

    :param orders: commandes issues de get_all_history_orders()
    :param date_from: borne de début incluse (None = pas de borne)
    :param date_to: borne de fin incluse (None = pas de borne)
    :return: dict avec "par_heure" (24 tranches horaires) et "totaux" (répartition
        par statut des commandes prises en compte).
    """
    par_heure: Dict[int, int] = defaultdict(int)
    nb_terminees = 0
    nb_annulees = 0
    nb_en_cours = 0

    for order in orders:
        dt_validation = _horodatage(order.get("validation_at"))
        if dt_validation is None:
            continue
        if not _dans_periode(dt_validation, date_from, date_to):
            continue

        par_heure[dt_validation.hour] += 1

        statut = (order.get("status") or "").lower()
        if statut == "terminée":
            nb_terminees += 1
        elif statut == "annulée":
            nb_annulees += 1
        else:
            nb_en_cours += 1

    liste_par_heure = [
        {"heure": f"{h:02d}h", "quantite": par_heure.get(h, 0)}
        for h in range(24)
    ]

    return {
        "par_heure": liste_par_heure,
        "totaux": {
            "nb_commandes_validees": nb_terminees + nb_annulees + nb_en_cours,
            "nb_terminees": nb_terminees,
            "nb_annulees": nb_annulees,
            "nb_en_cours": nb_en_cours,
        },
    }


def _ventiler_par_plat(durees_par_plat: Dict[str, List[float]]) -> List[Dict[str, Any]]:
    """Construit la liste triée {plat, nb_plats, temps_moyen/min/max_minutes} à partir de durées en minutes."""
    resultat = [
        {
            "plat": plat,
            "nb_plats": len(durees),
            "temps_moyen_minutes": round(sum(durees) / len(durees), 1),
            "temps_min_minutes": round(min(durees), 1),
            "temps_max_minutes": round(max(durees), 1),
        }
        for plat, durees in durees_par_plat.items()
        if durees
    ]
    resultat.sort(key=lambda p: p["nb_plats"], reverse=True)
    return resultat


def _ventiler_par_heure(durees_par_plat_heure: Dict[str, Dict[int, List[float]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Construit, pour chaque plat, la liste {heure, temps_moyen_minutes, nb_plats} des tranches horaires
    ayant au moins une mesure (les heures creuses sont omises)."""
    return {
        plat: [
            {
                "heure": f"{h:02d}h",
                "temps_moyen_minutes": round(sum(durees) / len(durees), 1),
                "nb_plats": len(durees),
            }
            for h, durees in sorted(par_heure.items())
            if durees
        ]
        for plat, par_heure in durees_par_plat_heure.items()
    }


def calculer_temps_preparation(
    orders: List[Dict[str, Any]],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calcule le temps de préparation par type de plat (validation de la commande → plat "Prêt").

    Le point de départ est la validation de la commande (tous les plats passent en
    "En préparation" à cet instant) ; le point d'arrivée est la mise à disposition du
    plat ("Date de mise en livraison"). Les plats annulés avant d'avoir été prêts
    (jamais passés par "Prêt") ne sont pas comptabilisés, faute de durée mesurable.

    :param orders: commandes issues de get_all_history_orders()
    :param date_from: borne de début incluse sur la date de validation (None = pas de borne)
    :param date_to: borne de fin incluse sur la date de validation (None = pas de borne)
    :return: dict avec "par_plat" (liste triée par nombre de plats), "temps_moyen_global_minutes"
        et "par_plat_et_heure" (ventilation horaire par plat, basée sur l'heure de validation).
    """
    durees_par_plat: Dict[str, List[float]] = defaultdict(list)
    durees_par_plat_heure: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    toutes_durees: List[float] = []

    for order in orders:
        dt_validation = _horodatage(order.get("validation_at"))
        if dt_validation is None:
            continue
        if not _dans_periode(dt_validation, date_from, date_to):
            continue

        for item in order.get("items", []):
            dt_pret = _horodatage(item.get("ready_at"))
            if dt_pret is None:
                continue
            duree_minutes = (dt_pret - dt_validation).total_seconds() / 60
            if duree_minutes < 0:
                continue

            type_plat = item.get("plat") or item.get("nom") or "Inconnu"
            durees_par_plat[type_plat].append(duree_minutes)
            durees_par_plat_heure[type_plat][dt_validation.hour].append(duree_minutes)
            toutes_durees.append(duree_minutes)

    return {
        "par_plat": _ventiler_par_plat(durees_par_plat),
        "temps_moyen_global_minutes": round(sum(toutes_durees) / len(toutes_durees), 1) if toutes_durees else 0,
        "par_plat_et_heure": _ventiler_par_heure(durees_par_plat_heure),
    }


def calculer_delais_livraison(
    orders: List[Dict[str, Any]],
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Calcule le délai de retrait par type de plat (plat "Prêt" → remise au client "Livré").

    Mesure le temps pendant lequel un plat prêt a attendu que le client vienne le
    chercher. Seuls les plats effectivement livrés (avec une date de mise à
    disposition et une date de livraison) sont comptabilisés.

    :param orders: commandes issues de get_all_history_orders()
    :param date_from: borne de début incluse sur la date de validation (None = pas de borne)
    :param date_to: borne de fin incluse sur la date de validation (None = pas de borne)
    :return: dict avec "par_plat" (liste triée par nombre de plats), "temps_moyen_global_minutes"
        et "par_plat_et_heure" (ventilation horaire par plat, basée sur l'heure de mise à disposition).
    """
    durees_par_plat: Dict[str, List[float]] = defaultdict(list)
    durees_par_plat_heure: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    toutes_durees: List[float] = []

    for order in orders:
        dt_validation = _horodatage(order.get("validation_at"))
        if dt_validation is None:
            continue
        if not _dans_periode(dt_validation, date_from, date_to):
            continue

        for item in order.get("items", []):
            dt_pret = _horodatage(item.get("ready_at"))
            dt_livre = _horodatage(item.get("delivered_at"))
            if dt_pret is None or dt_livre is None:
                continue
            duree_minutes = (dt_livre - dt_pret).total_seconds() / 60
            if duree_minutes < 0:
                continue

            type_plat = item.get("plat") or item.get("nom") or "Inconnu"
            durees_par_plat[type_plat].append(duree_minutes)
            durees_par_plat_heure[type_plat][dt_pret.hour].append(duree_minutes)
            toutes_durees.append(duree_minutes)

    return {
        "par_plat": _ventiler_par_plat(durees_par_plat),
        "temps_moyen_global_minutes": round(sum(toutes_durees) / len(toutes_durees), 1) if toutes_durees else 0,
        "par_plat_et_heure": _ventiler_par_heure(durees_par_plat_heure),
    }
