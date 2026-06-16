#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
imprimante.py - Configuration de l'imprimante thermique

Description:
    Lecture de la configuration imprimante (assets/config.json) avec valeurs
    par défaut, et conversion des identifiants USB (hex string ou entier).

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


# Valeurs par défaut imprimante
_DEFAULT_PRINTER = {
    "vendor_id": "0x04B8",
    "product_id": "0x0E15",
    "interface": 0,
    "modele": "TM-T20II",
}


def _parse_hex_or_int(value: Any, default: int) -> int:
    """Convertit une valeur hex string ('0x04B8') ou entier en int."""
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 16) if value.startswith("0x") or value.startswith("0X") else int(value)
        except ValueError:
            pass
    return default


def get_printer_config() -> Dict[str, Any]:
    """Retourne la configuration de l'imprimante thermique avec les valeurs par défaut si absente."""
    from src.backend.config.persistance import _load_app_config

    config = _load_app_config()
    printer = config.get("imprimante", {})
    return {
        "vendor_id": _parse_hex_or_int(printer.get("vendor_id", _DEFAULT_PRINTER["vendor_id"]), 0x04B8),
        "product_id": _parse_hex_or_int(printer.get("product_id", _DEFAULT_PRINTER["product_id"]), 0x0E15),
        "interface": int(printer.get("interface", _DEFAULT_PRINTER["interface"])),
        "modele": str(printer.get("modele", _DEFAULT_PRINTER["modele"])),
    }
