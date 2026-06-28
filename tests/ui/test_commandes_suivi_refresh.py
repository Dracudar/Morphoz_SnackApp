#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_commandes_suivi_refresh.py - Tests UI du rafraîchissement incrémental du suivi

Description:
    Vérifie le court-circuit de signature et le diff de cartes du widget
    ConteneurSuiviCommande : un tick sans changement ne reconstruit rien, et
    seules les cartes modifiées sont reconstruites.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.27
"""

import pytest

from src.modules.commandes_suivi.UI.widgets import conteneur_suivi_commande as mod
from src.modules.commandes_suivi.UI.widgets.conteneur_suivi_commande import (
    ConteneurSuiviCommande,
)


def _commande(order_id, items, priority=False):
    return {
        "id": order_id,
        "priority": priority,
        "pending_count": len(items),
        "items": items,
    }


@pytest.fixture
def tracker(qtbot, monkeypatch):
    """Tracker avec sources de données simulées et contrôlables."""
    etat = {"orders": [], "sig": ()}
    monkeypatch.setattr(mod, "get_live_orders", lambda: etat["orders"])
    monkeypatch.setattr(mod, "signature_live_orders", lambda: etat["sig"])
    widget = ConteneurSuiviCommande()
    qtbot.addWidget(widget)
    widget._etat = etat
    return widget


class TestSuiviDiff:
    def test_ajout_de_cartes(self, tracker):
        tracker._etat["orders"] = [
            _commande("C1", [{"id": "P001", "status": "En préparation"}]),
            _commande("C2", [{"id": "G001", "status": "Prêt"}]),
        ]
        tracker._etat["sig"] = (("a", 1),)
        tracker.refresh_orders()
        assert set(tracker._cards.keys()) == {"C1", "C2"}
        assert tracker._displayed_order == ["C1", "C2"]

    def test_court_circuit_conserve_les_widgets(self, tracker):
        tracker._etat["orders"] = [_commande("C1", [{"id": "P001", "status": "Prêt"}])]
        tracker._etat["sig"] = (("a", 1),)
        tracker.refresh_orders()
        carte = tracker._cards["C1"]
        # Signature inchangée -> court-circuit : même objet conservé
        tracker.refresh_orders()
        assert tracker._cards["C1"] is carte

    def test_modif_reconstruit_seulement_la_carte_concernee(self, tracker):
        tracker._etat["orders"] = [
            _commande("C1", [{"id": "P001", "status": "En préparation"}]),
            _commande("C2", [{"id": "G001", "status": "En préparation"}]),
        ]
        tracker._etat["sig"] = (("a", 1),)
        tracker.refresh_orders()
        c1, c2 = tracker._cards["C1"], tracker._cards["C2"]

        # Seule C1 change de statut
        tracker._etat["orders"][0]["items"][0]["status"] = "Prêt"
        tracker._etat["sig"] = (("a", 2),)
        tracker.refresh_orders()
        assert tracker._cards["C1"] is not c1   # reconstruite
        assert tracker._cards["C2"] is c2       # intacte

    def test_suppression_de_carte(self, tracker):
        tracker._etat["orders"] = [
            _commande("C1", [{"id": "P001", "status": "Prêt"}]),
            _commande("C2", [{"id": "G001", "status": "Prêt"}]),
        ]
        tracker._etat["sig"] = (("a", 1),)
        tracker.refresh_orders()

        tracker._etat["orders"] = [tracker._etat["orders"][0]]
        tracker._etat["sig"] = (("a", 2),)
        tracker.refresh_orders()
        assert set(tracker._cards.keys()) == {"C1"}

    def test_etat_collapse_preserve_au_refresh(self, tracker):
        tracker._etat["orders"] = [_commande("C1", [{"id": "P001", "status": "Prêt"}])]
        tracker._etat["sig"] = (("a", 1),)
        tracker.refresh_orders()
        tracker._expanded_orders.add("C1")  # déplié

        # Un changement de données ne doit pas perdre l'état déplié
        tracker._etat["orders"][0]["items"][0]["status"] = "Livré"
        tracker._etat["sig"] = (("a", 2),)
        tracker.refresh_orders()
        assert "C1" in tracker._expanded_orders
