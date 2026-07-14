#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_sumup.py - Tests unitaires pour le rapprochement SumUp

Description:
    Tests unitaires pour src/modules/stats/backend/sumup.py.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.07.13

Date de modification:
    2026.07.13
"""

from datetime import datetime

from src.modules.stats.backend.sumup import (
    _corriger_encodage,
    _parser_date_sumup,
    _parser_montant,
    comptes_disponibles,
    grouper_transactions,
    horodatage_commande,
    lire_lignes_csv,
    rapprocher_paiements_carte,
    suggerer_commandes_probables,
)


def _commande_carte(id_, date, heure, montant):
    return {"id": id_, "datetime": horodatage_commande([date, heure]), "montant": montant}


def _transaction(reference, dt, montant, moyen="Carte", lisible=True):
    return {
        "reference": reference,
        "datetime": dt,
        "montant": montant,
        "moyen_paiement": moyen,
        "lisible": lisible,
    }


def _commande(id_, date, heure, montant, payment_type="Espèces"):
    return {
        "id": id_,
        "datetime": horodatage_commande([date, heure]),
        "montant": montant,
        "payment_type": payment_type,
    }


# ── _corriger_encodage ──────────────────────────────────────────────────────

def test_corriger_encodage_mojibake():
    assert _corriger_encodage("RÃ©f. transaction") == "Réf. transaction"


def test_corriger_encodage_texte_propre_inchange():
    assert _corriger_encodage("Réf. transaction") == "Réf. transaction"


# ── _parser_montant ──────────────────────────────────────────────────────────

def test_parser_montant_point_decimal():
    assert _parser_montant("12.50") == 12.50


def test_parser_montant_virgule_decimale():
    assert _parser_montant("12,50") == 12.50


def test_parser_montant_milliers_et_decimale():
    assert _parser_montant("1.234,56") == 1234.56


def test_parser_montant_invalide():
    assert _parser_montant("abc") == 0.0


def test_parser_montant_vide():
    assert _parser_montant("") == 0.0


# ── _parser_date_sumup ────────────────────────────────────────────────────────

def test_parser_date_sumup_format_slash_secondes():
    assert _parser_date_sumup("13/07/2026 14:32:10") == datetime(2026, 7, 13, 14, 32, 10)


def test_parser_date_sumup_format_point():
    assert _parser_date_sumup("13.07.2026 14:32") == datetime(2026, 7, 13, 14, 32)


def test_parser_date_sumup_format_iso():
    assert _parser_date_sumup("2026-07-13T14:32:10") == datetime(2026, 7, 13, 14, 32, 10)


def test_parser_date_sumup_invalide():
    assert _parser_date_sumup("pas une date") is None


# ── horodatage_commande ───────────────────────────────────────────────────────

def test_horodatage_commande_valide():
    assert horodatage_commande(["13/07/2026", "14:32"]) == datetime(2026, 7, 13, 14, 32)


def test_horodatage_commande_vide():
    assert horodatage_commande(["", ""]) is None


def test_horodatage_commande_type_invalide():
    assert horodatage_commande("pas une liste") is None


# ── lire_lignes_csv / comptes_disponibles ─────────────────────────────────────

def test_lire_lignes_csv_corrige_encodage(tmp_path):
    entete = "Date,Type,Réf. transaction,Moyen de paiement,Quantité,Prix (TTC),Compte"
    ligne = "13/07/2026 14:32:10,Vente,TX1,Carte,1,5.00,SnackTPE"
    chemin = tmp_path / "releve.csv"
    # Simule le mojibake réel du CR SumUp : les octets UTF-8 corrects ont été
    # relus comme du Latin-1 puis ré-encodés en UTF-8 avant écriture du fichier.
    texte_correct = entete + "\n" + ligne + "\n"
    chemin.write_bytes(texte_correct.encode("utf-8").decode("latin-1").encode("utf-8"))

    lignes = lire_lignes_csv(str(chemin))
    assert len(lignes) == 1
    assert lignes[0]["Réf. transaction"] == "TX1"
    assert lignes[0]["Compte"] == "SnackTPE"


def test_comptes_disponibles():
    lignes = [{"Compte": "SnackTPE"}, {"Compte": "BuvetteTPE"}, {"Compte": "SnackTPE"}, {"Compte": ""}]
    assert comptes_disponibles(lignes) == ["BuvetteTPE", "SnackTPE"]


# ── grouper_transactions ──────────────────────────────────────────────────────

def test_grouper_transactions_filtre_compte():
    lignes = [
        {"Compte": "SnackTPE", "Réf. transaction": "TX1", "Date": "13/07/2026 14:00", "Prix (TTC)": "5.00", "Moyen de paiement": "Carte"},
        {"Compte": "AutreTPE", "Réf. transaction": "TX2", "Date": "13/07/2026 14:05", "Prix (TTC)": "3.00", "Moyen de paiement": "Carte"},
    ]
    transactions = grouper_transactions(lignes, "SnackTPE")
    assert len(transactions) == 1
    assert transactions[0]["reference"] == "TX1"


def test_grouper_transactions_regroupe_par_reference_et_somme_le_montant():
    lignes = [
        {"Compte": "SnackTPE", "Réf. transaction": "TX1", "Date": "13/07/2026 14:00:00", "Prix (TTC)": "5.00", "Moyen de paiement": "Carte"},
        {"Compte": "SnackTPE", "Réf. transaction": "TX1", "Date": "13/07/2026 14:00:05", "Prix (TTC)": "2.50", "Moyen de paiement": "Carte"},
    ]
    transactions = grouper_transactions(lignes, "SnackTPE")
    assert len(transactions) == 1
    assert transactions[0]["montant"] == 7.50
    assert transactions[0]["datetime"] == datetime(2026, 7, 13, 14, 0, 0)


def test_grouper_transactions_reference_vide_ne_fusionne_pas():
    lignes = [
        {"Compte": "SnackTPE", "Réf. transaction": "", "Date": "13/07/2026 14:00", "Prix (TTC)": "5.00"},
        {"Compte": "SnackTPE", "Réf. transaction": "", "Date": "13/07/2026 14:05", "Prix (TTC)": "3.00"},
    ]
    transactions = grouper_transactions(lignes, "SnackTPE")
    assert len(transactions) == 2


def test_grouper_transactions_date_illisible_marquee_non_lisible():
    lignes = [{"Compte": "SnackTPE", "Réf. transaction": "TX1", "Date": "n'importe quoi", "Prix (TTC)": "5.00"}]
    transactions = grouper_transactions(lignes, "SnackTPE")
    assert transactions[0]["lisible"] is False


# ── rapprocher_paiements_carte ────────────────────────────────────────────────

def test_rapprochement_associe_montant_et_date_proches():
    commandes = [_commande_carte("C1", "13/07/2026", "14:03", 5.00)]
    transactions = [_transaction("TX1", datetime(2026, 7, 13, 14, 0, 30), 5.00)]

    resultat = rapprocher_paiements_carte(commandes, transactions, tolerance_minutes=5)

    assert len(resultat["paires"]) == 1
    assert resultat["commandes_sans_correspondance"] == []
    assert resultat["transactions_sans_correspondance"] == []


def test_rapprochement_hors_tolerance_temporelle():
    commandes = [_commande_carte("C1", "13/07/2026", "14:10", 5.00)]
    transactions = [_transaction("TX1", datetime(2026, 7, 13, 14, 0, 0), 5.00)]

    resultat = rapprocher_paiements_carte(commandes, transactions, tolerance_minutes=5)

    assert resultat["paires"] == []
    assert len(resultat["commandes_sans_correspondance"]) == 1
    assert len(resultat["transactions_sans_correspondance"]) == 1


def test_rapprochement_montant_different_ne_matche_pas():
    commandes = [_commande_carte("C1", "13/07/2026", "14:00", 5.00)]
    transactions = [_transaction("TX1", datetime(2026, 7, 13, 14, 0, 0), 6.00)]

    resultat = rapprocher_paiements_carte(commandes, transactions, tolerance_minutes=5)

    assert resultat["paires"] == []
    assert len(resultat["commandes_sans_correspondance"]) == 1
    assert len(resultat["transactions_sans_correspondance"]) == 1


def test_rapprochement_choisit_la_correspondance_la_plus_proche():
    commandes = [_commande_carte("C1", "13/07/2026", "14:00", 5.00)]
    transactions = [
        _transaction("TX1", datetime(2026, 7, 13, 14, 4, 0), 5.00),
        _transaction("TX2", datetime(2026, 7, 13, 14, 0, 30), 5.00),
    ]

    resultat = rapprocher_paiements_carte(commandes, transactions, tolerance_minutes=5)

    assert len(resultat["paires"]) == 1
    assert resultat["paires"][0]["transaction"]["reference"] == "TX2"
    assert len(resultat["transactions_sans_correspondance"]) == 1
    assert resultat["transactions_sans_correspondance"][0]["reference"] == "TX1"


def test_rapprochement_ignore_transactions_illisibles():
    commandes = [_commande_carte("C1", "13/07/2026", "14:00", 5.00)]
    transactions = [_transaction("TX1", None, 5.00, lisible=False)]

    resultat = rapprocher_paiements_carte(commandes, transactions, tolerance_minutes=5)

    assert resultat["paires"] == []
    assert len(resultat["commandes_sans_correspondance"]) == 1
    assert len(resultat["transactions_sans_correspondance"]) == 1


def test_rapprochement_ignore_commandes_sans_date():
    commandes = [{"id": "C1", "datetime": None, "montant": 5.00}]
    transactions = [_transaction("TX1", datetime(2026, 7, 13, 14, 0, 0), 5.00)]

    resultat = rapprocher_paiements_carte(commandes, transactions, tolerance_minutes=5)

    assert resultat["paires"] == []
    assert len(resultat["commandes_sans_correspondance"]) == 1


# ── suggerer_commandes_probables ──────────────────────────────────────────────

def test_suggestion_trouve_une_commande_espece_au_montant_et_a_l_heure_proches():
    transaction = _transaction("TX1", datetime(2026, 7, 13, 14, 0, 0), 5.00)
    commandes = [_commande("C1", "13/07/2026", "14:02", 5.00, payment_type="Espèces")]

    suggestions = suggerer_commandes_probables([transaction], commandes, tolerance_minutes=5)

    assert len(suggestions["TX1"]) == 1
    assert suggestions["TX1"][0]["id"] == "C1"
    assert suggestions["TX1"][0]["payment_type"] == "Espèces"
    assert suggestions["TX1"][0]["ecart_minutes"] == 2.0


def test_suggestion_montant_different_exclu():
    transaction = _transaction("TX1", datetime(2026, 7, 13, 14, 0, 0), 5.00)
    commandes = [_commande("C1", "13/07/2026", "14:00", 6.00, payment_type="Espèces")]

    suggestions = suggerer_commandes_probables([transaction], commandes, tolerance_minutes=5)

    assert suggestions["TX1"] == []


def test_suggestion_hors_tolerance_temporelle_exclue():
    transaction = _transaction("TX1", datetime(2026, 7, 13, 14, 0, 0), 5.00)
    commandes = [_commande("C1", "13/07/2026", "14:10", 5.00, payment_type="Espèces")]

    suggestions = suggerer_commandes_probables([transaction], commandes, tolerance_minutes=5)

    assert suggestions["TX1"] == []


def test_suggestion_triee_par_ecart_croissant():
    transaction = _transaction("TX1", datetime(2026, 7, 13, 14, 0, 0), 5.00)
    commandes = [
        _commande("C1", "13/07/2026", "14:04", 5.00, payment_type="Espèces"),
        _commande("C2", "13/07/2026", "14:01", 5.00, payment_type="Repas gratuit"),
    ]

    suggestions = suggerer_commandes_probables([transaction], commandes, tolerance_minutes=5)

    assert [c["id"] for c in suggestions["TX1"]] == ["C2", "C1"]


def test_suggestion_transaction_illisible_sans_candidat():
    transaction = _transaction("TX1", None, 5.00, lisible=False)
    commandes = [_commande("C1", "13/07/2026", "14:00", 5.00, payment_type="Espèces")]

    suggestions = suggerer_commandes_probables([transaction], commandes, tolerance_minutes=5)

    assert suggestions["TX1"] == []
