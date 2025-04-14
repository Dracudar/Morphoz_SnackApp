import json

def charger_donnees_stock(stock_file_path):
    """
    Charge les données du fichier JSON de stock.

    :param stock_file_path: Chemin vers le fichier JSON de stock.
    :return: Données du fichier sous forme de dictionnaire.
    """
    try:
        with open(stock_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier de stock '{stock_file_path}' est introuvable.")
    except json.JSONDecodeError:
        raise ValueError(f"Le fichier de stock '{stock_file_path}' contient des données invalides.")

def charger_donnees_menu(menu_file_path):
    """
    Charge les données du fichier JSON de menu.

    :param menu_file_path: Chemin vers le fichier JSON de menu.
    :return: Données du fichier sous forme de dictionnaire.
    """
    try:
        with open(menu_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Le fichier de menu '{menu_file_path}' est introuvable.")
    except json.JSONDecodeError:
        raise ValueError(f"Le fichier de menu '{menu_file_path}' contient des données invalides.")