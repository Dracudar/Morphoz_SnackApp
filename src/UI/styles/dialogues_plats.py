#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
styles_plats.py

Description:
    Feuilles de style (QSS) communes aux dialogues de personnalisation des plats
    (pizza, grillade, crêpe, salade composée). Centralise les styles partagés
    pour éviter leur duplication entre les fichiers `*_dialog.py`.

Author :
    Dracudar

Version:
    1.0

Date de création :
    2026.06.19

Date de modification:
    2026.06.19
"""

# ── Styles communs aux dialogues ────────────────────────────────────────────────

DIALOG_STYLE = """
    QDialog {
        background-color: #2f3136;
    }
    QWidget {
        background-color: #2f3136;
        color: #f5f5f5;
    }
    QScrollArea, QScrollArea > QWidget > QWidget {
        background-color: #2f3136;
    }
"""

BTN_STYLE = """
    QPushButton {
        background-color: #4f545e;
        border: 2px solid #7d8390;
        border-radius: 8px;
        color: #f5f5f5;
        font-size: 13px;
        font-weight: 600;
        padding: 8px 16px;
        min-height: 38px;
    }
    QPushButton:hover { background-color: #626978; border-color: #8fa3b6; }
    QPushButton:pressed { background-color: #3a3d43; }
    QPushButton:disabled { color: #8f949c; background-color: #3a3d43; border-color: #595d64; }
"""

VALIDATE_BTN_STYLE = """
    QPushButton {
        background-color: #3a7a3a;
        border: 2px solid #4d9c4d;
        border-radius: 8px;
        color: #f5f5f5;
        font-size: 14px;
        font-weight: 700;
        padding: 10px 24px;
        min-height: 44px;
    }
    QPushButton:hover { background-color: #4d9c4d; }
    QPushButton:pressed { background-color: #2e5e2e; }
"""

TITLE_STYLE = "font-size: 18px; font-weight: 700; color: #f5f5f5;"
SECTION_STYLE = "font-size: 14px; font-weight: 700; color: #f5f5f5;"
CATEGORY_STYLE = "font-size: 12px; font-weight: 700; color: #a8d08d; margin-top: 6px;"
PRICE_STYLE = "font-size: 11px; color: #a8d08d;"
PRIX_TOTAL_STYLE = "font-size: 13px; font-weight: 600; color: #a8d08d; padding: 4px 0;"
WARNING_STYLE = "font-size: 12px; color: #e07070; padding: 2px 0;"

SUPPLEMENT_VIANDE = 1.0  # € par viande sélectionnée (salade, pizza)


def style_bouton_toggle(font_size: int, padding: str, min_height: int, text_align: str = "") -> str:
    """Style QSS d'un bouton à bascule (ingrédient/garniture/accompagnement).

    Les dialogues partagent la même apparence (transparent, coché = inversion
    des couleurs) mais avec des dimensions propres à chaque type de plat.
    """
    ligne_alignement = f"text-align: {text_align};" if text_align else ""
    return f"""
        QPushButton {{
            background-color: transparent;
            border: 2px solid #7d8390;
            border-radius: 5px;
            color: #f5f5f5;
            font-size: {font_size}px;
            padding: {padding};
            min-height: {min_height}px;
            {ligne_alignement}
        }}
        QPushButton:hover {{
            border-color: #c0c0c0;
        }}
        QPushButton:checked {{
            background-color: #f5f5f5;
            border-color: #f5f5f5;
            color: #2f3136;
            font-weight: 600;
        }}
    """
