#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detail_commande.py

Description:
    Actions sur les commandes et plats depuis l'historique : réimpression
    des tickets récap/cuisine, changement de statut (Prêt, Livré) et
    annulation (plat ou commande complète), avec confirmation utilisateur.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.16

Date de modification:
    2026.06.16
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import QMessageBox

from src.backend.impression.reimprimer import reprint_all_active_cuisine, reprint_ticket_cuisine_plat, reprint_ticket_recap
from src.backend.suivi.commandes_suivi_gestion import (
    annuler_commande_complete,
    annuler_plat_valide,
    marquer_plat_livre,
    marquer_plat_pret,
)


class _DetailCommandeMixin:
    """Méthodes d'action sur les commandes/plats, mélangées dans CommandesHistoriqueModule."""

    def _on_print_recap(self, order: Dict[str, Any]):
        """Réimprime le ticket récapitulatif de la commande."""
        try:
            reprint_ticket_recap(str(order["file"]))
        except Exception as e:
            QMessageBox.warning(self, "Impression", f"Erreur d'impression :\n{e}")

    def _on_print_cuisine_plat(self, order: Dict[str, Any], item: Dict[str, Any]):
        """Réimprime le ticket cuisine d'un plat spécifique."""
        try:
            reprint_ticket_cuisine_plat(str(order["file"]), item["id"])
        except Exception as e:
            QMessageBox.warning(self, "Impression", f"Erreur d'impression :\n{e}")

    def _on_print_all_active(self):
        """Imprime les tickets cuisine de tous les plats en préparation ou prêts."""
        try:
            count = reprint_all_active_cuisine()
            if count == 0:
                QMessageBox.information(self, "Impression", "Aucun plat en préparation ou prêt.")
            else:
                QMessageBox.information(
                    self,
                    "Impression",
                    f"{count} ticket{'s' if count > 1 else ''} cuisine imprimé{'s' if count > 1 else ''}.",
                )
        except Exception as e:
            QMessageBox.warning(self, "Impression", f"Erreur d'impression :\n{e}")

    def _on_marquer_pret(self, order: Dict[str, Any], item: Dict[str, Any]):
        """Passe le plat au statut Prêt et rafraîchit l'affichage."""
        marquer_plat_pret(str(order["file"]), item["id"])
        self.refresh_orders()

    def _on_marquer_livre(self, order: Dict[str, Any], item: Dict[str, Any]):
        """Passe le plat directement au statut Livré (depuis En préparation ou Prêt) et rafraîchit."""
        marquer_plat_livre(str(order["file"]), item["id"])
        self.refresh_orders()

    def _on_annuler_plat(self, order: Dict[str, Any], item: Dict[str, Any]):
        """Demande confirmation puis annule le plat avec horodatage."""
        nom_plat = item.get("nom") or item.get("plat") or item["id"]
        reponse = QMessageBox.question(
            self,
            "Confirmer l'annulation",
            f"Annuler le plat « {nom_plat} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reponse == QMessageBox.StandardButton.Yes:
            annuler_plat_valide(str(order["file"]), item["id"])
            self.refresh_orders()

    def _on_annuler_commande(self, order: Dict[str, Any]):
        """Demande confirmation puis annule tous les plats restants de la commande."""
        reponse = QMessageBox.question(
            self,
            "Confirmer l'annulation",
            f"Annuler tous les plats restants de la commande « {order.get('id', '')} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reponse == QMessageBox.StandardButton.Yes:
            annuler_commande_complete(str(order["file"]))
            self.refresh_orders()
