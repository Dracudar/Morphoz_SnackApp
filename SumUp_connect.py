import requests

# Configuration SumUp
SUMUP_ACCESS_TOKEN = "votre_access_token"  # Remplacez par votre jeton d'accès
SUMUP_API_URL = "https://api.sumup.com/v0.1/checkouts"

def envoyer_paiement(total):
    headers = {
        "Authorization": f"Bearer {SUMUP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "amount": total,
        "currency": "EUR",
        "checkout_reference": "Commande123",  # Référence unique pour la commande
        "description": "Paiement commande SnackApp"
    }
    response = requests.post(SUMUP_API_URL, headers=headers, json=data)
    if response.status_code == 201:
        print("Paiement envoyé au terminal SumUp.")
    else:
        print(f"Erreur lors de l'envoi du paiement : {response.json()}")

# Exemple d'utilisation
envoyer_paiement(total)

