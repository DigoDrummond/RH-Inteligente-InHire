"""
Script para registrar webhook na API Inhire
apontando para Google Chat

COMO USAR:
1. Execute: python registrar_webhook_google_chat.py
2. Script vai criar webhook apontando para o Google Chat
3. Teste criando uma candidatura na Inhire
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
    "description": "Notifica no Google Chat quando há nova candidatura",
    "event": "JOB_TALENT_ADDED",  # Evento de nova candidatura
    "url": GOOGLE_CHAT_URL,
    "enabled": True
}


# ========================================
# FUNÇÕES
# ========================================

def autenticar():
    """Autentica na API Inhire e retorna token de acesso"""
    print(">> Autenticando na API Inhire...")

    response = requests.post(
        f"{INHIRE_AUTH_URL}/login",
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


def validar_configuracao():
    """Valida se configurações foram preenchidas"""
    erros = []

    if not INHIRE_EMAIL:
        erros.append("ERRO: INHIRE_EMAIL nao encontrado no .env")

    if not INHIRE_PASSWORD:
        erros.append("ERRO: INHIRE_PASSWORD nao encontrado no .env")

    if erros:
        print("\nAVISO: CONFIGURACAO INCOMPLETA:\n")
        for erro in erros:
            print(f"  {erro}")
        print("\nConfigure as variaveis no arquivo .env\n")
        sys.exit(1)


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
    print("CONFIGURACAO DE WEBHOOK INHIRE -> GOOGLE CHAT")
    print("="*70 + "\n")

    # 1. Validar configuração
    validar_configuracao()

    # 2. Testar Google Chat primeiro
    if not testar_google_chat():
        print("\nAVISO: URL do Google Chat parece invalida")
        resposta = input("Deseja continuar mesmo assim? (s/n): ").strip().lower()
        if resposta != 's':
            print("\nOperacao cancelada\n")
            sys.exit(0)

    # 3. Exibir resumo
    print("\n" + "="*70)
    print("RESUMO DA CONFIGURACAO")
    print("="*70)
    print(f"\nURL do Google Chat:")
    print(f"   {GOOGLE_CHAT_URL[:60]}...")
    print(f"\nEvento a monitorar:")
    print(f"   {WEBHOOK_CONFIG['event']} - {WEBHOOK_CONFIG['description']}")
    print("\n" + "="*70 + "\n")

    # 4. Confirmar
    resposta = input("Deseja criar o webhook na Inhire? (s/n): ").strip().lower()
    if resposta != 's':
        print("\nOperacao cancelada pelo usuario\n")
        sys.exit(0)

    # 5. Autenticar
    token = autenticar()

    # 6. Listar webhooks existentes
    existing = listar_webhooks_existentes(token)

    # 7. Verificar se já existe webhook para este evento
    webhook_existente = None
    for wh in existing:
        if wh.get('event') == WEBHOOK_CONFIG['event']:
            webhook_existente = wh
            break

    if webhook_existente:
        print(f"\nAVISO: Ja existe webhook para o evento {WEBHOOK_CONFIG['event']}")
        print(f"   Nome: {webhook_existente.get('name')}")
        print(f"   URL: {webhook_existente.get('url')[:60]}...")

        resposta = input("\nDeseja substituir? (s/n): ").strip().lower()
        if resposta == 's':
            # Deletar o antigo
            deletar_webhook(token, webhook_existente.get('id'))
            # Criar novo
            criar_webhook(token, WEBHOOK_CONFIG)
        else:
            print("\nOperacao cancelada\n")
            sys.exit(0)
    else:
        # Criar novo
        criar_webhook(token, WEBHOOK_CONFIG)

    # 8. Resumo final
    print("\n" + "="*70)
    print("OK CONFIGURACAO CONCLUIDA!")
    print("="*70)
    print("\nProximos passos:")
    print("   1. Crie uma nova candidatura na Inhire")
    print("   2. Verifique se a notificacao aparece no Google Chat")
    print("   3. Os dados virao no formato JSON do webhook Inhire")
    print("\nDica:")
    print("   O Google Chat recebera dados brutos (JSON)")
    print("   Para formatar melhor, considere criar um intermediario")
    print("   (Google Apps Script ou Cloud Function)")
    print("\nWebhook configurado!\n")


if __name__ == "__main__":
    main()
