import requests
import secrets

# 1. PEGA TU TOKEN AQUÍ
access_token = secrets.linkedin_access_token
author_urn = secrets.linkedin_user_urn

url = "https://api.linkedin.com/rest/posts" 

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "LinkedIn-Version": "202601", # Usa la versión actual
    "X-Restli-Protocol-Version": "2.0.0"
}

payload = {
    "author": author_urn,
    "commentary": "Este post ha sido enviado desde código a mi perfil personal 🚀 #Python #LinkedInAPI",
    "visibility": "PUBLIC",
    "distribution": {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": False
}

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 201:
    print("¡Post publicado con éxito en tu perfil!")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

# Telegram ID 8317541333:AAGT2qi0stCKgv9fjQTf76LX-njqtIroNis