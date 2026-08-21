"""
Teste REAL de Webhook - Passo a Passo

Este script vai guiar voce no teste de webhook real
"""

import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

GOOGLE_CHAT_URL = "https://chat.googleapis.com/v1/spaces/AAQAq3TELWs/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=cQNn23zrgwi7Ts60xLFf1Std_AaKlvLujR3hywd3NIU"

INHIRE_AUTH_URL = os.getenv("INHIRE_AUTH_URL", "https://auth.inhire.app")
INHIRE_API_URL = os.getenv("INHIRE_API_URL", "https://api.inhire.app")
INHIRE_EMAIL = os.getenv("INHIRE_EMAIL")
INHIRE_PASSWORD = os.getenv("INHIRE_PASSWORD")
INHIRE_TENANT = os.getenv("INHIRE_TENANT", "frameworkdigital")

print("\n" + "="*70)
print("TESTE REAL DE WEBHOOK - PASSO A PASSO")
print("="*70 + "\n")

# Autenticar
print(">> Autenticando na Inhire...")
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
print("OK Autenticado!\n")

# Buscar vagas abertas
print(">> Buscando vagas abertas...")
headers = {
    "Authorization": f"Bearer {token}",
    "X-Tenant": INHIRE_TENANT,
    "Content-Type": "application/json"
}

response = requests.get(
    f"{INHIRE_API_URL}/jobs",
    headers=headers,
    params={"status": "open"}
)

if response.status_code == 200:
    jobs = response.json()
    print(f"OK {len(jobs)} vagas abertas encontradas!\n")

    if jobs:
        print("VAGAS DISPONIVEIS:")
        for i, job in enumerate(jobs[:5], 1):  # Mostrar apenas 5
            print(f"{i}. {job.get('name')}")
            print(f"   ID: {job.get('id')}")
            print(f"   Status: {job.get('status')}")
            print()

        print("="*70)
        print("INSTRUCOES PARA TESTE:")
        print("="*70 + "\n")

        print("OPCAO 1: CRIAR CANDIDATURA VIA PAGINA DE CARREIRAS")
        print("-" * 70)
        print("1. Acesse a pagina de carreiras da Framework")
        print("2. Encontre uma das vagas acima")
        print("3. Preencha o formulario de candidatura:")
        print("   - Nome: Teste Webhook")
        print("   - Email: teste.webhook@framework.com.br")
        print("   - Telefone: (11) 99999-9999")
        print("4. Envie a candidatura")
        print("5. AGUARDE 10 SEGUNDOS")
        print("6. Verifique o Google Chat - deve chegar a notificacao!")
        print()

        print("OPCAO 2: CRIAR CANDIDATURA VIA PLATAFORMA INHIRE")
        print("-" * 70)
        print("1. Acesse: https://app.inhire.app")
        print("2. Va em 'Vagas' ou 'Candidatos'")
        print("3. Adicione um novo candidato a uma vaga")
        print("4. AGUARDE 10 SEGUNDOS")
        print("5. Verifique o Google Chat - deve chegar a notificacao!")
        print()

        print("OPCAO 3: MOVER CANDIDATO DE ETAPA")
        print("-" * 70)
        print("1. Acesse: https://app.inhire.app")
        print("2. Va em uma vaga que JA TENHA candidatos")
        print("3. Arraste um candidato para outra etapa")
        print("   (Ex: Triagem -> Entrevista)")
        print("4. AGUARDE 10 SEGUNDOS")
        print("5. Verifique o Google Chat - deve chegar a notificacao!")
        print()

        print("="*70)
        print("IMPORTANTE:")
        print("="*70 + "\n")
        print("1. Os webhooks APENAS disparam para NOVOS eventos")
        print("   - Candidaturas antigas: NAO vao disparar")
        print("   - Mudancas antigas: NAO vao disparar")
        print()
        print("2. O webhook envia dados em formato JSON bruto")
        print("   - Vai chegar uma mensagem tipo:")
        print('     {"event": "JOB_TALENT_ADDED", "data": {...}}')
        print()
        print("3. Se NAO chegar notificacao:")
        print("   - Verifique se o evento realmente ocorreu na Inhire")
        print("   - Aguarde ate 30 segundos (pode ter delay)")
        print("   - Tente criar OUTRA candidatura")
        print()

        print("="*70)
        print("AGUARDANDO VOCE TESTAR...")
        print("="*70)
        print()
        print("Deixe esta janela aberta e faca o teste.")
        print("Quando terminar, pressione ENTER para verificar logs.")
        print()

        input("Pressione ENTER apos criar a candidatura/mover candidato...")

        print("\n>> Verificando se webhook foi disparado...")
        print("(Infelizmente a API Inhire nao expoe logs de webhooks)")
        print()

        # Enviar mensagem confirmacao
        payload = {
            "text": "Verificacao de teste concluida. Se voce criou uma candidatura e NAO recebeu notificacao antes desta mensagem, o webhook pode nao estar funcionando."
        }

        requests.post(
            GOOGLE_CHAT_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        print("="*70)
        print("RESULTADO DO TESTE:")
        print("="*70 + "\n")

        print("VOCE RECEBEU A NOTIFICACAO DA CANDIDATURA/MUDANCA?")
        print()
        print("SIM - O webhook esta funcionando perfeitamente!")
        print("      Todos os novos eventos serao notificados.")
        print()
        print("NAO - Possivel problema:")
        print("      1. Evento pode nao ter sido criado na Inhire")
        print("      2. Webhook pode ter delay (espere 1-2 minutos)")
        print("      3. Pode haver restricao/filtro na Inhire")
        print("      4. Formato do payload pode estar incompativel")
        print()

    else:
        print("AVISO: Nenhuma vaga aberta encontrada!")
        print("Crie uma vaga primeiro para testar.")
else:
    print(f"ERRO ao buscar vagas: {response.status_code}")

print("="*70 + "\n")
