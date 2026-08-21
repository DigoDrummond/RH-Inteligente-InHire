"""
Script para registrar TODOS os webhooks da Inhire
apontando para Google Chat

Registra os 5 eventos principais:
1. JOB_TALENT_ADDED - Novas candidaturas
2. JOB_TALENT_STAGE_ADDED - Mudancas de etapa
3. JOB_ADDED - Novas vagas
4. REQUISITION_STATUS_UPDATED - Status de requisicoes
5. FORM_RESPONSE_ADDED - Respostas de formularios
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
# CONFIGURAÇÃO DOS 5 WEBHOOKS
# ========================================

WEBHOOKS = [
    {
        "name": "GChat - Novas Candidaturas",
        "description": "Notifica quando ha nova candidatura",
        "event": "JOB_TALENT_ADDED",
        "url": GOOGLE_CHAT_URL
    },
    {
        "name": "GChat - Mudancas de Etapa",
        "description": "Notifica quando candidato muda de etapa",
        "event": "JOB_TALENT_STAGE_ADDED",
        "url": GOOGLE_CHAT_URL
    },
    {
        "name": "GChat - Novas Vagas",
        "description": "Notifica quando nova vaga e criada",
        "event": "JOB_ADDED",
        "url": GOOGLE_CHAT_URL
    },
    {
        "name": "GChat - Status de Requisicoes",
        "description": "Notifica quando status de requisicao muda",
        "event": "REQUISITION_STATUS_UPDATED",
        "url": GOOGLE_CHAT_URL
    },
    {
        "name": "GChat - Respostas de Formularios",
        "description": "Notifica quando formulario e preenchido",
        "event": "FORM_RESPONSE_ADDED",
        "url": GOOGLE_CHAT_URL
    }
]


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
        return {}

    webhooks = response.json()
    print(f"OK {len(webhooks)} webhooks encontrados")

    # Criar dicionário {evento: webhook}
    webhooks_dict = {}
    for wh in webhooks:
        webhooks_dict[wh.get('event')] = wh

    # Mostrar webhooks existentes
    if webhooks:
        print("\n>> Webhooks cadastrados:")
        for wh in webhooks:
            print(f"   - {wh.get('event')}: {wh.get('name')}")
            print(f"     Status: {'[ATIVO]' if wh.get('isActive', True) else '[INATIVO]'}")

    return webhooks_dict


def criar_webhook(token, webhook_config):
    """Cria novo webhook"""

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant": INHIRE_TENANT,
        "Content-Type": "application/json"
    }

    print(f"\n[+] Criando: {webhook_config['name']}")
    print(f"    Evento: {webhook_config['event']}")

    response = requests.post(
        f"{INHIRE_API_URL}/integrations/webhooks",
        headers=headers,
        json=webhook_config
    )

    if response.status_code in [200, 201]:
        print(f"    OK Webhook criado!")
        data = response.json()
        print(f"    ID: {data.get('id')}")
        return True, data.get('id')
    else:
        print(f"    ERRO: {response.status_code}")
        print(f"    Resposta: {response.text}")
        return False, None


def deletar_webhook(token, webhook_id):
    """Deleta webhook existente"""

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant": INHIRE_TENANT,
        "Content-Type": "application/json"
    }

    print(f"    Deletando webhook antigo (ID: {webhook_id[:8]}...)")

    response = requests.delete(
        f"{INHIRE_API_URL}/integrations/webhooks/{webhook_id}",
        headers=headers
    )

    if response.status_code in [200, 204]:
        print(f"    OK Deletado!")
        return True
    else:
        print(f"    ERRO ao deletar: {response.status_code}")
        return False


def testar_google_chat():
    """Testa envio para Google Chat"""
    print("\n[TEST] Testando envio para Google Chat...")

    payload = {
        "text": "Teste - Configuracao de 5 webhooks Inhire\nTodos os eventos serao notificados aqui!"
    }

    try:
        response = requests.post(
            GOOGLE_CHAT_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if response.status_code == 200:
            print("   OK Mensagem de teste enviada!")
            print("   Verifique o Google Chat")
            return True
        else:
            print(f"   ERRO: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ERRO: {e}")
        return False


# ========================================
# MAIN
# ========================================

def main():
    print("\n" + "="*70)
    print("CONFIGURACAO DE TODOS OS WEBHOOKS INHIRE -> GOOGLE CHAT")
    print("="*70)
    print(f"\nTotal de webhooks a configurar: {len(WEBHOOKS)}")
    print()
    for i, wh in enumerate(WEBHOOKS, 1):
        print(f"  {i}. {wh['event']:30s} - {wh['description']}")
    print("\n" + "="*70 + "\n")

    # 1. Testar Google Chat primeiro
    if not testar_google_chat():
        print("\nERRO: URL do Google Chat invalida")
        sys.exit(1)

    # 2. Autenticar
    token = autenticar()

    # 3. Listar webhooks existentes
    existing = listar_webhooks_existentes(token)

    # 4. Configurar cada webhook
    print("\n" + "="*70)
    print("CONFIGURANDO WEBHOOKS")
    print("="*70)

    resultados = {
        'criados': 0,
        'substituidos': 0,
        'erros': 0
    }

    for webhook in WEBHOOKS:
        evento = webhook['event']

        # Verificar se já existe
        if evento in existing:
            print(f"\n[!] Webhook existente: {evento}")
            print(f"    Nome antigo: {existing[evento].get('name')}")

            # Deletar o antigo
            if deletar_webhook(token, existing[evento].get('id')):
                # Criar novo
                sucesso, webhook_id = criar_webhook(token, webhook)
                if sucesso:
                    resultados['substituidos'] += 1
                else:
                    resultados['erros'] += 1
            else:
                resultados['erros'] += 1
        else:
            # Criar novo
            sucesso, webhook_id = criar_webhook(token, webhook)
            if sucesso:
                resultados['criados'] += 1
            else:
                resultados['erros'] += 1

    # 5. Resumo final
    print("\n" + "="*70)
    print("RESUMO DA CONFIGURACAO")
    print("="*70)
    print(f"\nWebhooks criados:      {resultados['criados']}")
    print(f"Webhooks substituidos: {resultados['substituidos']}")
    print(f"Erros:                 {resultados['erros']}")
    print(f"\nTotal configurado:     {resultados['criados'] + resultados['substituidos']}/{len(WEBHOOKS)}")

    if resultados['erros'] == 0:
        print("\n" + "="*70)
        print("OK TODOS OS WEBHOOKS CONFIGURADOS COM SUCESSO!")
        print("="*70)
        print("\nO QUE VAI ACONTECER AGORA:")
        print()
        print("1. NOVAS CANDIDATURAS")
        print("   - Toda vez que alguem se candidatar")
        print("   - Voce recebera notificacao instantanea no Google Chat")
        print()
        print("2. MUDANCAS DE ETAPA")
        print("   - Quando candidato mudar de etapa")
        print("   - Ex: Triagem -> Entrevista -> Proposta")
        print()
        print("3. NOVAS VAGAS")
        print("   - Quando vaga for criada no sistema")
        print()
        print("4. REQUISICOES")
        print("   - Quando status de requisicao mudar")
        print("   - Ex: Pendente -> Aprovada -> Rejeitada")
        print()
        print("5. FORMULARIOS")
        print("   - Quando candidato preencher formulario")
        print()
        print("="*70)
        print("\nCOMO TESTAR:")
        print("   1. Crie uma candidatura de teste na Inhire")
        print("   2. Mova o candidato de etapa")
        print("   3. Veja as notificacoes chegando no Google Chat")
        print()
        print("OBSERVACAO:")
        print("   Os dados virao em formato JSON (bruto)")
        print("   Para formatar melhor, considere usar intermediario")
        print("   (Google Apps Script ou Cloud Function)")
        print()
    else:
        print("\n" + "="*70)
        print("ATENCAO: Alguns webhooks falharam!")
        print("="*70)
        print("\nVerifique os erros acima e tente novamente.")
        print()


if __name__ == "__main__":
    main()
