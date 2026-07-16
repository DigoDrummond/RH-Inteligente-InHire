"""
Script para registrar webhooks na API Inhire
apontando para Google Apps Script (Google Sheets)

COMO USAR:
1. Configure APPS_SCRIPT_URL e SECRET_TOKEN abaixo
2. Execute: python registrar_webhooks_google_sheets.py
3. Script vai criar automaticamente os 5 webhooks
"""

import requests
import os
import sys
from dotenv import load_dotenv

# ========================================
# CONFIGURAÇÕES
# ========================================

# URL do seu Google Apps Script (Web App)
# Exemplo: https://script.google.com/macros/s/AKfycby...xyz123/exec
APPS_SCRIPT_URL = "https://script.google.com/macros/s/SEU_ID_AQUI/exec"

# Token secreto (mesmo que configurou no Apps Script)
SECRET_TOKEN = "SEU_TOKEN_SECRETO_AQUI"

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
# CONFIGURAÇÃO DOS WEBHOOKS
# ========================================

WEBHOOKS = [
    {
        "name": "Candidaturas para Google Sheets",
        "description": "Registra novas candidaturas automaticamente na planilha",
        "event": "JOB_TALENT_ADDED",
        "url": f"{APPS_SCRIPT_URL}/job-talent-added",
        "enabled": True
    },
    {
        "name": "Mudanças de Etapa para Google Sheets",
        "description": "Registra quando candidatos mudam de etapa",
        "event": "JOB_TALENT_STAGE_ADDED",
        "url": f"{APPS_SCRIPT_URL}/job-talent-stage-added",
        "enabled": True
    },
    {
        "name": "Novas Vagas para Google Sheets",
        "description": "Registra quando novas vagas são criadas",
        "event": "JOB_ADDED",
        "url": f"{APPS_SCRIPT_URL}/job-added",
        "enabled": True
    },
    {
        "name": "Formulários para Google Sheets",
        "description": "Registra respostas de formulários",
        "event": "FORM_RESPONSE_ADDED",
        "url": f"{APPS_SCRIPT_URL}/form-response-added",
        "enabled": True
    },
    {
        "name": "Requisições para Google Sheets",
        "description": "Registra mudanças de status de requisições",
        "event": "REQUISITION_STATUS_UPDATED",
        "url": f"{APPS_SCRIPT_URL}/requisition-status-updated",
        "enabled": True
    }
]


# ========================================
# FUNÇÕES
# ========================================

def autenticar():
    """Autentica na API Inhire e retorna token de acesso"""
    print("🔐 Autenticando na API Inhire...")

    response = requests.post(
        f"{INHIRE_AUTH_URL}/login",
        json={
            "email": INHIRE_EMAIL,
            "password": INHIRE_PASSWORD
        }
    )

    if response.status_code != 200:
        print(f"❌ Erro ao autenticar: {response.status_code}")
        print(response.text)
        sys.exit(1)

    token = response.json().get("accessToken")
    print(f"✅ Autenticado com sucesso!")

    return token


def listar_webhooks_existentes(token):
    """Lista webhooks já cadastrados"""
    print("\n📋 Listando webhooks existentes...")

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
        print(f"⚠️  Não foi possível listar webhooks: {response.status_code}")
        return {}

    webhooks = response.json()
    print(f"✅ {len(webhooks)} webhooks encontrados")

    # Criar dicionário {evento: webhook_id}
    return {wh.get("event"): wh for wh in webhooks}


def criar_ou_atualizar_webhook(token, webhook_config, existing_webhooks):
    """Cria novo webhook ou atualiza existente"""

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant": INHIRE_TENANT,
        "Content-Type": "application/json"
    }

    # Adicionar header de autenticação
    webhook_config["headers"] = {
        "Authorization": f"Bearer {SECRET_TOKEN}"
    }

    event = webhook_config["event"]

    # Verificar se já existe
    if event in existing_webhooks:
        # Atualizar
        webhook_id = existing_webhooks[event].get("id")
        print(f"\n🔄 Atualizando webhook: {webhook_config['name']}")

        response = requests.patch(
            f"{INHIRE_API_URL}/integrations/webhooks/{webhook_id}",
            headers=headers,
            json=webhook_config
        )

        if response.status_code in [200, 201]:
            print(f"   ✅ Webhook atualizado com sucesso!")
            print(f"   📍 Evento: {event}")
            print(f"   🔗 URL: {webhook_config['url']}")
        else:
            print(f"   ❌ Erro ao atualizar: {response.status_code}")
            print(f"   {response.text}")

    else:
        # Criar novo
        print(f"\n➕ Criando webhook: {webhook_config['name']}")

        response = requests.post(
            f"{INHIRE_API_URL}/integrations/webhooks",
            headers=headers,
            json=webhook_config
        )

        if response.status_code in [200, 201]:
            print(f"   ✅ Webhook criado com sucesso!")
            print(f"   📍 Evento: {event}")
            print(f"   🔗 URL: {webhook_config['url']}")
        else:
            print(f"   ❌ Erro ao criar: {response.status_code}")
            print(f"   {response.text}")


def validar_configuracao():
    """Valida se configurações foram preenchidas"""
    erros = []

    if "SEU_ID_AQUI" in APPS_SCRIPT_URL:
        erros.append("❌ APPS_SCRIPT_URL não foi configurada")

    if SECRET_TOKEN == "SEU_TOKEN_SECRETO_AQUI":
        erros.append("❌ SECRET_TOKEN não foi configurado")

    if not INHIRE_EMAIL:
        erros.append("❌ INHIRE_EMAIL não encontrado no .env")

    if not INHIRE_PASSWORD:
        erros.append("❌ INHIRE_PASSWORD não encontrado no .env")

    if erros:
        print("\n⚠️  CONFIGURAÇÃO INCOMPLETA:\n")
        for erro in erros:
            print(f"  {erro}")
        print("\n📝 Configure as variáveis no início do arquivo e no .env\n")
        sys.exit(1)


def exibir_resumo():
    """Exibe resumo da configuração"""
    print("\n" + "="*70)
    print("📊 RESUMO DA CONFIGURAÇÃO")
    print("="*70)
    print(f"\n🔗 URL do Apps Script:")
    print(f"   {APPS_SCRIPT_URL}")
    print(f"\n🔑 Token configurado:")
    print(f"   {SECRET_TOKEN[:20]}...{SECRET_TOKEN[-10:]}")
    print(f"\n📋 Webhooks a configurar: {len(WEBHOOKS)}")
    for i, wh in enumerate(WEBHOOKS, 1):
        print(f"   {i}. {wh['event']}")
    print("\n" + "="*70 + "\n")


# ========================================
# MAIN
# ========================================

def main():
    print("\n" + "="*70)
    print("🔔 CONFIGURAÇÃO DE WEBHOOKS INHIRE → GOOGLE SHEETS")
    print("="*70 + "\n")

    # 1. Validar configuração
    validar_configuracao()

    # 2. Exibir resumo
    exibir_resumo()

    # 3. Confirmar
    resposta = input("Deseja prosseguir? (s/n): ").strip().lower()
    if resposta != 's':
        print("\n❌ Operação cancelada pelo usuário\n")
        sys.exit(0)

    # 4. Autenticar
    token = autenticar()

    # 5. Listar webhooks existentes
    existing = listar_webhooks_existentes(token)

    # 6. Criar/atualizar webhooks
    print("\n🚀 Configurando webhooks...\n")

    for webhook in WEBHOOKS:
        criar_ou_atualizar_webhook(token, webhook, existing)

    # 7. Resumo final
    print("\n" + "="*70)
    print("✅ CONFIGURAÇÃO CONCLUÍDA!")
    print("="*70)
    print("\n📊 Próximos passos:")
    print("   1. Teste criando uma candidatura na Inhire")
    print("   2. Verifique se aparece na planilha Google Sheets")
    print("   3. Confira a aba 'Log de Eventos' para debug")
    print("\n🎉 Tudo pronto! Sua planilha será atualizada em tempo real!\n")


if __name__ == "__main__":
    main()
