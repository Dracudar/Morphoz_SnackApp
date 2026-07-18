#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_stats.py - Tests unitaires pour le module de statistiques

Description:
    Tests unitaires pour src/modules/stats/backend/stats.py.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.05

Date de modification:
    2026.07.16
"""

from datetime import datetime

from src.mod.stats.backend.stats import (
    calculer_affluence,
    calculer_composition_par_plat,
    calculer_delais_livraison,
    calculer_statistiques,
    calculer_temps_preparation,
)


def _commande(
    id_, statut="Terminée", montant=10.0, paiement="Espèces",
    date_creation="01/07/2026", items=None,
):
    return {
        "id": id_,
        "status": statut,
        "created_at": [date_creation, "12:00"],
        "amount": montant,
        "payment_type": paiement,
        "items": items or [],
    }


def _plat(plat="Pizza", statut="Livré", prix=8.0, recette="Margherita", composition=None):
    item = {"plat": plat, "nom": f"{plat}", "status": statut, "price": prix, "recette": recette}
    if composition is not None:
        item["composition"] = composition
    return item


def _commande_validee(
    id_, statut="Terminée", date_validation="01/07/2026", heure_validation="12:00", items=None,
):
    return {
        "id": id_,
        "status": statut,
        "validation_at": [date_validation, heure_validation],
        "items": items or [],
    }


def _plat_horodate(plat="Pizza", heure_pret=None, heure_livre=None, date="01/07/2026"):
    return {
        "plat": plat,
        "nom": plat,
        "ready_at": [date, heure_pret] if heure_pret else ["", ""],
        "delivered_at": [date, heure_livre] if heure_livre else ["", ""],
    }


class TestCalculerStatistiques:
    def test_liste_vide(self):
        stats = calculer_statistiques([])
        assert stats["totaux"] == {"nb_commandes": 0, "montant_total": 0, "nb_plats": 0, "panier_moyen": 0}
        assert stats["plats"] == []
        assert stats["paiements"] == []
        assert stats["recettes_pizza"] == []
        assert stats["ca_par_jour"] == []

    def test_ignore_commandes_non_terminees(self):
        orders = [
            _commande("1", statut="Validée"),
            _commande("2", statut="Annulée"),
        ]
        stats = calculer_statistiques(orders)
        assert stats["totaux"]["nb_commandes"] == 0

    def test_totaux_commandes_terminees(self):
        orders = [
            _commande("1", montant=10.0, items=[_plat()]),
            _commande("2", montant=20.0, items=[_plat(plat="Grillade", recette="")]),
        ]
        stats = calculer_statistiques(orders)
        assert stats["totaux"]["nb_commandes"] == 2
        assert stats["totaux"]["montant_total"] == 30.0
        assert stats["totaux"]["panier_moyen"] == 15.0
        assert stats["totaux"]["nb_plats"] == 2

    def test_exclut_plats_annules_de_la_commande(self):
        orders = [
            _commande("1", items=[_plat(), _plat(statut="Annulé")]),
        ]
        stats = calculer_statistiques(orders)
        assert stats["totaux"]["nb_plats"] == 1

    def test_ventilation_par_plat(self):
        orders = [
            _commande("1", items=[_plat(plat="Pizza", prix=8.0), _plat(plat="Pizza", prix=10.0)]),
        ]
        stats = calculer_statistiques(orders)
        assert len(stats["plats"]) == 1
        pizza = stats["plats"][0]
        assert pizza["nom"] == "Pizza"
        assert pizza["quantite"] == 2
        assert pizza["montant"] == 18.0
        assert pizza["prix_moyen"] == 9.0

    def test_ventilation_par_paiement(self):
        orders = [
            _commande("1", montant=10.0, paiement="Espèces"),
            _commande("2", montant=20.0, paiement="Carte"),
            _commande("3", montant=5.0, paiement="Espèces"),
        ]
        stats = calculer_statistiques(orders)
        paiements = {p["type"]: p for p in stats["paiements"]}
        assert paiements["Espèces"]["quantite"] == 2
        assert paiements["Espèces"]["montant"] == 15.0
        assert round(paiements["Espèces"]["pourcentage"], 1) == round(2 / 3 * 100, 1)
        assert paiements["Carte"]["quantite"] == 1

    def test_recettes_pizza_retire_suffixe_modifie(self):
        orders = [
            _commande("1", items=[_plat(recette="Reine - Modifié !")]),
            _commande("2", items=[_plat(recette="Reine")]),
        ]
        stats = calculer_statistiques(orders)
        recettes = {r["recette"]: r for r in stats["recettes_pizza"]}
        assert "Reine - Modifié !" not in recettes
        assert recettes["Reine"]["quantite"] == 2
        assert recettes["Reine"]["pourcentage"] == 100.0

    def test_recettes_pizza_ignore_autres_plats(self):
        orders = [_commande("1", items=[_plat(plat="Grillade", recette="")])]
        stats = calculer_statistiques(orders)
        assert stats["recettes_pizza"] == []

    def test_ca_par_jour_trie_chronologiquement(self):
        orders = [
            _commande("1", date_creation="03/07/2026", montant=5.0),
            _commande("2", date_creation="01/07/2026", montant=7.0),
            _commande("3", date_creation="02/07/2026", montant=3.0),
        ]
        stats = calculer_statistiques(orders)
        dates = [j["date"] for j in stats["ca_par_jour"]]
        assert dates == ["01/07/2026", "02/07/2026", "03/07/2026"]

    def test_filtre_periode(self):
        orders = [
            _commande("1", date_creation="01/07/2026", montant=10.0),
            _commande("2", date_creation="05/07/2026", montant=20.0),
            _commande("3", date_creation="10/07/2026", montant=30.0),
        ]
        stats = calculer_statistiques(
            orders,
            date_from=datetime(2026, 7, 2),
            date_to=datetime(2026, 7, 9),
        )
        assert stats["totaux"]["nb_commandes"] == 1
        assert stats["totaux"]["montant_total"] == 20.0

    def test_filtre_periode_borne_debut_incluse(self):
        orders = [_commande("1", date_creation="01/07/2026", montant=10.0)]
        stats = calculer_statistiques(orders, date_from=datetime(2026, 7, 1))
        assert stats["totaux"]["nb_commandes"] == 1

    def test_filtre_periode_borne_fin_incluse(self):
        orders = [_commande("1", date_creation="01/07/2026", montant=10.0, )]
        stats = calculer_statistiques(orders, date_to=datetime(2026, 7, 1, 23, 59))
        assert stats["totaux"]["nb_commandes"] == 1


class TestCalculerAffluence:
    def test_liste_vide(self):
        stats = calculer_affluence([])
        assert stats["par_heure"] == [{"heure": f"{h:02d}h", "quantite": 0} for h in range(24)]
        assert stats["totaux"] == {
            "nb_commandes_validees": 0, "nb_terminees": 0, "nb_annulees": 0, "nb_en_cours": 0,
        }

    def test_ignore_commandes_non_validees(self):
        orders = [{"id": "1", "status": "Terminée", "items": []}]
        stats = calculer_affluence(orders)
        assert stats["totaux"]["nb_commandes_validees"] == 0

    def test_repartition_par_heure(self):
        orders = [
            _commande_validee("1", heure_validation="12:15"),
            _commande_validee("2", heure_validation="12:45"),
            _commande_validee("3", heure_validation="19:00"),
        ]
        stats = calculer_affluence(orders)
        par_heure = {p["heure"]: p["quantite"] for p in stats["par_heure"]}
        assert par_heure["12h"] == 2
        assert par_heure["19h"] == 1
        assert par_heure["08h"] == 0

    def test_prend_en_compte_les_commandes_annulees(self):
        """Une commande annulée a bien été validée : elle compte dans l'affluence."""
        orders = [
            _commande_validee("1", statut="Terminée"),
            _commande_validee("2", statut="Annulée"),
        ]
        stats = calculer_affluence(orders)
        assert stats["totaux"]["nb_commandes_validees"] == 2
        assert stats["totaux"]["nb_terminees"] == 1
        assert stats["totaux"]["nb_annulees"] == 1
        assert sum(p["quantite"] for p in stats["par_heure"]) == 2

    def test_filtre_periode_sur_date_validation(self):
        orders = [
            _commande_validee("1", date_validation="01/07/2026"),
            _commande_validee("2", date_validation="10/07/2026"),
        ]
        stats = calculer_affluence(orders, date_from=datetime(2026, 7, 5))
        assert stats["totaux"]["nb_commandes_validees"] == 1

    def test_par_jour_ventile_par_date_sans_cumuler(self):
        """Deux commandes à la même heure mais des jours différents ne doivent pas se cumuler
        dans la même tranche horaire d'un jour donné."""
        orders = [
            _commande_validee("1", date_validation="01/07/2026", heure_validation="12:00"),
            _commande_validee("2", date_validation="02/07/2026", heure_validation="12:00"),
        ]
        stats = calculer_affluence(orders)
        assert [j["date"] for j in stats["par_jour"]] == ["01/07/2026", "02/07/2026"]
        for jour in stats["par_jour"]:
            par_heure = {p["heure"]: p["quantite"] for p in jour["par_heure"]}
            assert par_heure["12h"] == 1
        assert sum(p["quantite"] for p in stats["par_heure"]) == 2

    def test_par_jour_trie_chronologiquement(self):
        orders = [
            _commande_validee("1", date_validation="10/07/2026"),
            _commande_validee("2", date_validation="01/07/2026"),
        ]
        stats = calculer_affluence(orders)
        assert [j["date"] for j in stats["par_jour"]] == ["01/07/2026", "10/07/2026"]

    def test_par_jour_totaux_par_statut(self):
        orders = [
            _commande_validee("1", date_validation="01/07/2026", statut="Terminée"),
            _commande_validee("2", date_validation="01/07/2026", statut="Annulée"),
        ]
        stats = calculer_affluence(orders)
        totaux_jour = stats["par_jour"][0]["totaux"]
        assert totaux_jour == {
            "nb_commandes_validees": 2, "nb_terminees": 1, "nb_annulees": 1, "nb_en_cours": 0,
        }

    def test_par_jour_vide_si_aucune_commande(self):
        assert calculer_affluence([])["par_jour"] == []

    def test_par_semaine_regroupe_par_lundi(self):
        """01/07/2026 et 02/07/2026 tombent dans la même semaine ISO (lundi 29/06/2026) ;
        10/07/2026 est dans la semaine suivante (lundi 06/07/2026)."""
        orders = [
            _commande_validee("1", date_validation="01/07/2026"),
            _commande_validee("2", date_validation="02/07/2026"),
            _commande_validee("3", date_validation="10/07/2026"),
        ]
        stats = calculer_affluence(orders)
        par_semaine = {s["semaine"]: s["quantite"] for s in stats["par_semaine"]}
        assert par_semaine == {
            "Sem. 29/06": 2,
            "Sem. 06/07": 1,
        }
        assert [s["semaine"] for s in stats["par_semaine"]] == ["Sem. 29/06", "Sem. 06/07"]

    def test_par_mois_regroupe_par_mois(self):
        orders = [
            _commande_validee("1", date_validation="01/07/2026"),
            _commande_validee("2", date_validation="15/07/2026"),
            _commande_validee("3", date_validation="02/08/2026"),
        ]
        stats = calculer_affluence(orders)
        par_mois = {m["mois"]: m["quantite"] for m in stats["par_mois"]}
        assert par_mois == {"07/2026": 2, "08/2026": 1}
        assert [m["mois"] for m in stats["par_mois"]] == ["07/2026", "08/2026"]

    def test_moyenne_par_jour(self):
        orders = [
            _commande_validee("1", date_validation="01/07/2026"),
            _commande_validee("2", date_validation="01/07/2026"),
            _commande_validee("3", date_validation="02/07/2026"),
        ]
        stats = calculer_affluence(orders)
        assert stats["moyenne_par_jour"] == 1.5

    def test_moyenne_par_jour_zero_si_aucune_commande(self):
        assert calculer_affluence([])["moyenne_par_jour"] == 0.0


class TestCalculerTempsPreparation:
    def test_liste_vide(self):
        stats = calculer_temps_preparation([])
        assert stats["par_plat"] == []
        assert stats["temps_moyen_global_minutes"] == 0

    def test_duree_entre_validation_et_pret(self):
        orders = [
            _commande_validee("1", heure_validation="12:00", items=[
                _plat_horodate("Pizza", heure_pret="12:20"),
            ]),
        ]
        stats = calculer_temps_preparation(orders)
        assert len(stats["par_plat"]) == 1
        pizza = stats["par_plat"][0]
        assert pizza["plat"] == "Pizza"
        assert pizza["nb_plats"] == 1
        assert pizza["temps_moyen_minutes"] == 20.0
        assert stats["temps_moyen_global_minutes"] == 20.0

    def test_ignore_plats_jamais_prets(self):
        """Un plat annulé avant d'avoir été prêt n'a pas de durée mesurable."""
        orders = [
            _commande_validee("1", items=[_plat_horodate("Pizza", heure_pret=None)]),
        ]
        stats = calculer_temps_preparation(orders)
        assert stats["par_plat"] == []

    def test_moyenne_min_max_par_type_de_plat(self):
        orders = [
            _commande_validee("1", heure_validation="12:00", items=[
                _plat_horodate("Pizza", heure_pret="12:10"),
                _plat_horodate("Pizza", heure_pret="12:30"),
            ]),
        ]
        stats = calculer_temps_preparation(orders)
        pizza = stats["par_plat"][0]
        assert pizza["nb_plats"] == 2
        assert pizza["temps_min_minutes"] == 10.0
        assert pizza["temps_max_minutes"] == 30.0
        assert pizza["temps_moyen_minutes"] == 20.0

    def test_ignore_commandes_non_validees(self):
        orders = [{"id": "1", "items": [_plat_horodate("Pizza", heure_pret="12:10")]}]
        stats = calculer_temps_preparation(orders)
        assert stats["par_plat"] == []


class TestCalculerDelaisLivraison:
    def test_liste_vide(self):
        stats = calculer_delais_livraison([])
        assert stats["par_plat"] == []
        assert stats["temps_moyen_global_minutes"] == 0

    def test_duree_entre_pret_et_livre(self):
        orders = [
            _commande_validee("1", items=[
                _plat_horodate("Pizza", heure_pret="12:00", heure_livre="12:07"),
            ]),
        ]
        stats = calculer_delais_livraison(orders)
        pizza = stats["par_plat"][0]
        assert pizza["nb_plats"] == 1
        assert pizza["temps_moyen_minutes"] == 7.0
        assert stats["temps_moyen_global_minutes"] == 7.0

    def test_ignore_plats_non_livres(self):
        orders = [
            _commande_validee("1", items=[
                _plat_horodate("Pizza", heure_pret="12:00", heure_livre=None),
            ]),
        ]
        stats = calculer_delais_livraison(orders)
        assert stats["par_plat"] == []

    def test_montant_absent_traite_comme_zero(self):
        orders = [_commande("1", montant=0.0)]
        orders[0]["amount"] = None
        stats = calculer_statistiques(orders)
        assert stats["totaux"]["montant_total"] == 0


class TestCalculerCompositionParPlat:
    def test_liste_vide(self):
        assert calculer_composition_par_plat([]) == {}

    def test_ignore_plats_sans_composition(self):
        orders = [_commande("1", items=[_plat(plat="Frites", composition=[])])]
        assert calculer_composition_par_plat(orders) == {}

    def test_grillade_viandes_et_accompagnement(self):
        orders = [
            _commande("1", items=[_plat(
                plat="Grillade",
                composition={"Viandes": {"Merguez": 2, "Poulet": 1}, "Accompagnement": "Frites"},
            )]),
            _commande("2", items=[_plat(
                plat="Grillade",
                composition={"Viandes": {"Merguez": 1}, "Accompagnement": "Sans"},
            )]),
        ]
        composition = calculer_composition_par_plat(orders)
        assert composition["Grillade"]["viandes"] == [
            {"nom": "Merguez", "quantite": 3}, {"nom": "Poulet", "quantite": 1},
        ]
        # "Sans" accompagnement n'est pas comptabilisé comme un choix.
        assert composition["Grillade"]["accompagnements"] == [{"nom": "Frites", "quantite": 1}]

    def test_crepe_garnitures(self):
        orders = [
            _commande("1", items=[_plat(plat="Crêpe", composition={"Garniture": ["Nutella"]})]),
            _commande("2", items=[_plat(plat="Crêpe", composition={"Garniture": []})]),
        ]
        composition = calculer_composition_par_plat(orders)
        assert composition["Crêpe"]["garnitures"] == [{"nom": "Nutella", "quantite": 1}]

    def test_salade_ingredients(self):
        orders = [
            _commande("1", items=[_plat(
                plat="Salade composée",
                composition={"Ingrédients": ["Tomate", "Feta"]},
            )]),
        ]
        composition = calculer_composition_par_plat(orders)
        assert composition["Salade composée"]["ingredients"] == [
            {"nom": "Tomate", "quantite": 1}, {"nom": "Feta", "quantite": 1},
        ]

    def test_pizza_ajouts_et_retraits(self):
        orders = [
            _commande("1", items=[_plat(
                plat="Pizza",
                composition={"Base": "Tomate", "Ingrédients": [], "Ajouts": ["Champignons"], "Retraits": ["Olives"]},
            )]),
        ]
        composition = calculer_composition_par_plat(orders)
        assert composition["Pizza"]["ajouts"] == [{"nom": "Champignons", "quantite": 1}]
        assert composition["Pizza"]["retraits"] == [{"nom": "Olives", "quantite": 1}]

    def test_exclut_plats_annules(self):
        orders = [
            _commande("1", items=[_plat(
                plat="Grillade", statut="Annulé",
                composition={"Viandes": {"Merguez": 1}, "Accompagnement": "Frites"},
            )]),
        ]
        assert calculer_composition_par_plat(orders) == {}

    def test_ignore_commandes_non_terminees(self):
        orders = [_commande("1", statut="Validée", items=[_plat(
            plat="Grillade", composition={"Viandes": {"Merguez": 1}, "Accompagnement": "Frites"},
        )])]
        assert calculer_composition_par_plat(orders) == {}

    def test_filtre_periode(self):
        orders = [
            _commande("1", date_creation="01/07/2026", items=[_plat(
                plat="Grillade", composition={"Viandes": {"Merguez": 1}, "Accompagnement": "Frites"},
            )]),
            _commande("2", date_creation="10/07/2026", items=[_plat(
                plat="Grillade", composition={"Viandes": {"Poulet": 1}, "Accompagnement": "Sans"},
            )]),
        ]
        composition = calculer_composition_par_plat(orders, date_from=datetime(2026, 7, 5))
        assert composition["Grillade"]["viandes"] == [{"nom": "Poulet", "quantite": 1}]
