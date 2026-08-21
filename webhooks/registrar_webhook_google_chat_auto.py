"""
Script para registrar webhook na API Inhire
apontando para Google Chat (EXECUCAO AUTOMATICA)

COMO USAR:
Execute: python registrar_webhook_google_chat_auto.py
"""

import requests
import os
import sys
from dotenv import load_dotenv

# ========================================
# CONFIGURAÇÕES
# ========================================

# URL do Google Chat Webhook
GOOGLE_CHAT_URL = "https://chat.googleapis.com/v1/spaces/AAQAq3TELWs/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=cQNn23zrgwi7Ts60xLFf1Std_AaKlvLujR3hywd3NIU"

# ========================================
# CARREGAR CREDENCIAIS INHIRE
# ========================================

load_dotenv()

INHIRE_AUTH_URL = os.getenv("INHIRE_AUTH_URL", "https://auth.inhire.app")
INHIRE_API_URL = os.getenv("INHIRE_API_URL", "https://api.inhire.app")
INHIRE_EMAIL = os.getenv("INHIRE_EMAIL")
INHIRE_PASSWORD = os.getenv("INHIRE_PASSWORD")
INHIRE_TENANT = os.getenv("INHIRE_TENANT", "frameworkdigital")


# ========================================
# CONFIGURAÇÃO DO WEBHOOK
# ========================================

WEBHOOK_CONFIG = {
    "name": "Candidaturas para Google Chat",
    "description": "Notifica no Google Chat quando ha nova candidatura",
    "event": "JOB_TALENT_ADDED",
    "url": GOOGLE_CHAT_URL
}


# ========================================
# FUNÇÕES
# ========================================

def autenticar():
    """Autentica na API Inhire e retorna token de acesso"""
    print(">> Autenticando na API Inhire...")

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

    if response.status_code != 200:
        print(f"ERRO ao autenticar: {response.status_code}")
        print(response.text)
        sys.exit(1)

    token = response.json().get("accessToken")
    print(f"OK Autenticado com sucesso!")

    return token


def listar_webhooks_existentes(token):
    """Lista webhooks já cadastrados"""
    print("\n>> Listando webhooks existentes...")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant": INHIRE_TENANT,
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"{INHIRE_API_URL}/integrations/webhooks",
        headers=headers
    )

    if response.status_code != 200:
        print(f"AVISO: Nao foi possivel listar webhooks: {response.status_code}")
        return []

    webhooks = response.json()
    print(f"OK {len(webhooks)} webhooks encontrados")

    # Mostrar webhooks existentes
    if webhooks:
        print("\n>> Webhooks cadastrados:")
        for wh in webhooks:
            print(f"   - {wh.get('event')}: {wh.get('name')}")
            print(f"     URL: {wh.get('url')[:60]}...")
            print(f"     Status: {'[ATIVO]' if wh.get('enabled') else '[INATIVO]'}")

    return webhooks


def criar_webhook(token, webhook_config):
    """Cria novo webhook"""

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant": INHIRE_TENANT,
        "Content-Type": "application/json"
    }

    print(f"\n[+] Criando webhook: {webhook_config['name']}")
    print(f"    Evento: {webhook_config['event']}")
    print(f"    URL: {webhook_config['url'][:60]}...")

    response = requests.post(
        f"{INHIRE_API_URL}/integrations/webhooks",
        headers=headers,
        json=webhook_config
    )

    if response.status_code in [200, 201]:
        print(f"    OK Webhook criado com sucesso!")
        data = response.json()
        print(f"    ID: {data.get('id')}")
        return True
    else:
        print(f"    ERRO ao criar: {response.status_code}")
        print(f"    Resposta: {response.text}")
        return False


def deletar_webhook(token, webhook_id):
    """Deleta webhook existente"""

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant": INHIRE_TENANT,
        "Content-Type": "application/json"
    }

    print(f"\n[-] Deletando webhook ID: {webhook_id}")

    response = requests.delete(
        f"{INHIRE_API_URL}/integrations/webhooks/{webhook_id}",
        headers=headers
    )

    if response.status_code in [200, 204]:
        print(f"    OK Webhook deletado com sucesso!")
        return True
    else:
        print(f"    ERRO ao deletar: {response.status_code}")
        return False


def testar_google_chat():
    """Testa envio para Google Chat"""
    print("\n[TEST] Testando envio para Google Chat...")

    payload = {
        "text": "Teste de webhook Inhire -> Google Chat\nSistema configurado com sucesso!"
    }

    try:
        response = requests.post(
            GOOGLE_CHAT_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            print("   OK Mensagem de teste enviada com sucesso!")
            print("   Verifique o Google Chat")
            return True
        else:
            print(f"   ERRO ao enviar: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False

    except Exception as e:
        print(f"   ERRO: {e}")
        return False


# ========================================
# MAIN
# ========================================

def main():
    print("\n" + "="*70)
    print("CONFIGURACAO AUTOMATICA DE WEBHOOK INHIRE -> GOOGLE CHAT")
    print("="*70 + "\n")

    # 1. Testar Google Chat primeiro
    if not testar_google_chat():
        print("\nERRO: URL do Google Chat invalida")
        sys.exit(1)

    # 2. Autenticar
    token = autenticar()

    # 3. Listar webhooks existentes
    existing = listar_webhooks_existentes(token)

    # 4. Verificar se já existe webhook para este evento
    webhook_existente = None
    for wh in existing:
        if wh.get('event') == WEBHOOK_CONFIG['event']:
            webhook_existente = wh
            break

    if webhook_existente:
        print(f"\n>> Webhook existente encontrado: {WEBHOOK_CONFIG['event']}")
        print(f"   Nome: {webhook_existente.get('name')}")
        print(f"   URL antiga: {webhook_existente.get('url')[:60]}...")
        print(f"   URL nova:   {WEBHOOK_CONFIG['url'][:60]}...")

        # Deletar o antigo automaticamente
        deletar_webhook(token, webhook_existente.get('id'))

    # 5. Criar novo webhook
    sucesso = criar_webhook(token, WEBHOOK_CONFIG)

    # 6. Resumo final
    print("\n" + "="*70)
    if sucesso:
        print("OK WEBHOOK CONFIGURADO COM SUCESSO!")
    else:
        print("ERRO AO CONFIGURAR WEBHOOK")
    print("="*70)

    if sucesso:
        print("\nProximos passos:")
        print("   1. Crie uma nova candidatura na Inhire")
        print("   2. Verifique se a notificacao aparece no Google Chat")
        print("\nOBSERVACAO:")
        print("   O Google Chat recebera dados brutos (JSON da Inhire)")
        print("   Para formatar melhor, use Google Apps Script como intermediario")
        print()


if __name__ == "__main__":
    main()
