"""
Cria apenas o webhook de candidaturas (JOB_TALENT_ADDED)
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CHAT_URL = "https://chat.googleapis.com/v1/spaces/AAQAq3TELWs/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=cQNn23zrgwi7Ts60xLFf1Std_AaKlvLujR3hywd3NIU"

INHIRE_AUTH_URL = os.getenv("INHIRE_AUTH_URL", "https://auth.inhire.app")
INHIRE_API_URL = os.getenv("INHIRE_API_URL", "https://api.inhire.app")
INHIRE_EMAIL = os.getenv("INHIRE_EMAIL")
INHIRE_PASSWORD = os.getenv("INHIRE_PASSWORD")
INHIRE_TENANT = os.getenv("INHIRE_TENANT", "frameworkdigital")

print("\n>> Criando webhook: JOB_TALENT_ADDED")

# Autenticar
response = requests.post(
    f"{INHIRE_AUTH_URL}/login",
    headers={
        "X-Tenant": INHIRE_TENANT,
        "Content-Type": "application/json"
    },
    json={
        "email": INHIRE_EMAIL,
        "password": INHIRE_PASSWORD
    }
)

token = response.json().get("accessToken")

# Criar webhook
headers = {
    "Authorization": f"Bearer {token}",
    "X-Tenant": INHIRE_TENANT,
    "Content-Type": "application/json"
}

webhook_config = {
    "name": "GChat - Novas Candidaturas",
    "description": "Notifica quando ha nova candidatura",
    "event": "JOB_TALENT_ADDED",
    "url": GOOGLE_CHAT_URL
}

response = requests.post(
    f"{INHIRE_API_URL}/integrations/webhooks",
    headers=headers,
    json=webhook_config
)

if response.status_code in [200, 201]:
    data = response.json()
    print(f"OK Webhook criado com sucesso!")
    print(f"ID: {data.get('id')}")
else:
    print(f"ERRO: {response.status_code}")
    print(response.text)
