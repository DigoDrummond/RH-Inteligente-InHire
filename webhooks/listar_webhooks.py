"""
Lista todos os webhooks configurados na Inhire
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

INHIRE_AUTH_URL = os.getenv("INHIRE_AUTH_URL", "https://auth.inhire.app")
INHIRE_API_URL = os.getenv("INHIRE_API_URL", "https://api.inhire.app")
INHIRE_EMAIL = os.getenv("INHIRE_EMAIL")
INHIRE_PASSWORD = os.getenv("INHIRE_PASSWORD")
INHIRE_TENANT = os.getenv("INHIRE_TENANT", "frameworkdigital")

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

# Listar webhooks
headers = {
    "Authorization": f"Bearer {token}",
    "X-Tenant": INHIRE_TENANT,
    "Content-Type": "application/json"
}

response = requests.get(
    f"{INHIRE_API_URL}/integrations/webhooks",
    headers=headers
)

webhooks = response.json()

print("\n" + "="*70)
print(f"WEBHOOKS CONFIGURADOS NA INHIRE ({len(webhooks)} total)")
print("="*70 + "\n")

if webhooks:
    for i, wh in enumerate(webhooks, 1):
        print(f"{i}. {wh.get('name')}")
        print(f"   Evento: {wh.get('event')}")
        print(f"   URL:    {wh.get('url')[:50]}...")
        print(f"   ID:     {wh.get('id')}")
        print(f"   Status: {'[ATIVO]' if wh.get('isActive', True) else '[INATIVO]'}")
        print()
else:
    print("Nenhum webhook configurado")

print("="*70)
