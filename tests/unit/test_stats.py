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
    2026.07.05
"""

from datetime import datetime

from src.modules.stats.backend.stats import calculer_statistiques


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


def _plat(plat="Pizza", statut="Livré", prix=8.0, recette="Margherita"):
    return {"plat": plat, "nom": f"{plat}", "status": statut, "price": prix, "recette": recette}


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

    def test_montant_absent_traite_comme_zero(self):
        orders = [_commande("1", montant=0.0)]
        orders[0]["amount"] = None
        stats = calculer_statistiques(orders)
        assert stats["totaux"]["montant_total"] == 0
