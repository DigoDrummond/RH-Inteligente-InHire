"""
Script de Diagnostico de Webhooks
Verifica por que os webhooks nao estao funcionando
"""

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

GOOGLE_CHAT_URL = "https://chat.googleapis.com/v1/spaces/AAQAq3TELWs/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=cQNn23zrgwi7Ts60xLFf1Std_AaKlvLujR3hywd3NIU"

INHIRE_AUTH_URL = os.getenv("INHIRE_AUTH_URL", "https://auth.inhire.app")
INHIRE_API_URL = os.getenv("INHIRE_API_URL", "https://api.inhire.app")
INHIRE_EMAIL = os.getenv("INHIRE_EMAIL")
INHIRE_PASSWORD = os.getenv("INHIRE_PASSWORD")
INHIRE_TENANT = os.getenv("INHIRE_TENANT", "frameworkdigital")

print("\n" + "="*70)
print("DIAGNOSTICO DE WEBHOOKS")
print("="*70 + "\n")

# ====================
# TESTE 1: Google Chat
# ====================
print("[1/4] Testando URL do Google Chat...")

payload = {
    "text": "TESTE DE DIAGNOSTICO - " + str(os.popen("echo %TIME%").read().strip())
}

try:
    response = requests.post(
        GOOGLE_CHAT_URL,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )

    if response.status_code == 200:
        print("   OK Google Chat esta funcionando!")
        print("   Voce deve ter recebido uma mensagem agora")
    else:
        print(f"   ERRO: {response.status_code}")
        print(f"   Resposta: {response.text}")
        print("   PROBLEMA: URL do Google Chat invalida ou expirada")
except Exception as e:
    print(f"   ERRO: {e}")
    print("   PROBLEMA: Nao conseguiu conectar ao Google Chat")

print()

# ====================
# TESTE 2: Autenticacao Inhire
# ====================
print("[2/4] Testando autenticacao na Inhire...")

try:
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

    if response.status_code == 200:
        token = response.json().get("accessToken")
        print("   OK Autenticacao funcionando!")
    else:
        print(f"   ERRO: {response.status_code}")
        print("   PROBLEMA: Credenciais invalidas")
        exit(1)
except Exception as e:
    print(f"   ERRO: {e}")
    print("   PROBLEMA: Nao conseguiu conectar a API Inhire")
    exit(1)

print()

# ====================
# TESTE 3: Listar Webhooks
# ====================
print("[3/4] Verificando webhooks registrados...")

headers = {
    "Authorization": f"Bearer {token}",
    "X-Tenant": INHIRE_TENANT,
    "Content-Type": "application/json"
}

try:
    response = requests.get(
        f"{INHIRE_API_URL}/integrations/webhooks",
        headers=headers
    )

    if response.status_code == 200:
        webhooks = response.json()
        print(f"   OK {len(webhooks)} webhooks encontrados")
        print()

        if webhooks:
            print("   Webhooks registrados:")
            for wh in webhooks:
                print(f"   - {wh.get('event')}")
                print(f"     Nome: {wh.get('name')}")
                print(f"     URL:  {wh.get('url')[:60]}...")
                print(f"     ID:   {wh.get('id')}")

                # Verificar se esta ativo
                is_active = wh.get('isActive')
                if is_active is not None:
                    print(f"     Ativo: {is_active}")
                else:
                    print(f"     Ativo: (campo nao disponivel)")

                print()
        else:
            print("   PROBLEMA: Nenhum webhook registrado!")
    else:
        print(f"   ERRO: {response.status_code}")
        print("   PROBLEMA: Nao conseguiu listar webhooks")
except Exception as e:
    print(f"   ERRO: {e}")

print()

# ====================
# TESTE 4: Detalhes dos Webhooks
# ====================
print("[4/4] Verificando configuracao detalhada dos webhooks...")

if webhooks:
    for wh in webhooks:
        webhook_id = wh.get('id')

        try:
            response = requests.get(
                f"{INHIRE_API_URL}/integrations/webhooks/{webhook_id}",
                headers=headers
            )

            if response.status_code == 200:
                details = response.json()
                print(f"\n   Webhook: {details.get('event')}")
                print(f"   Configuracao completa:")
                print(f"   {json.dumps(details, indent=6, ensure_ascii=False)}")
            else:
                print(f"   ERRO ao buscar detalhes: {response.status_code}")
        except Exception as e:
            print(f"   ERRO: {e}")

print("\n" + "="*70)
print("RESUMO DO DIAGNOSTICO")
print("="*70 + "\n")

print("PROXIMOS PASSOS:")
print()
print("1. Verifique se recebeu a mensagem de teste no Google Chat")
print("   - Se NAO recebeu: URL do Google Chat esta incorreta/expirada")
print()
print("2. Verifique quantos webhooks estao registrados")
print("   - Esperado: 5 webhooks")
print("   - Se menos: Execute registrar_todos_webhooks_google_chat.py")
print()
print("3. Teste criando uma candidatura REAL na Inhire")
print("   - Acesse: https://app.inhire.app")
print("   - Crie uma candidatura de teste")
print("   - Aguarde 5-10 segundos")
print("   - Verifique o Google Chat")
print()
print("4. Se ainda nao funcionar:")
print("   - A Inhire pode ter limite de rate (muitos webhooks)")
print("   - A URL do Google Chat pode ter expirado")
print("   - O webhook pode estar com filtros/condicoes")
print()
print("="*70 + "\n")
