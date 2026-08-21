"""
Script para DELETAR webhooks da Inhire

Opcoes:
1. Deletar todos os webhooks do Google Chat
2. Deletar webhook especifico por evento
3. Deletar todos os webhooks
"""

import requests
import os
import sys
from dotenv import load_dotenv

load_dotenv()

INHIRE_AUTH_URL = os.getenv("INHIRE_AUTH_URL", "https://auth.inhire.app")
INHIRE_API_URL = os.getenv("INHIRE_API_URL", "https://api.inhire.app")
INHIRE_EMAIL = os.getenv("INHIRE_EMAIL")
INHIRE_PASSWORD = os.getenv("INHIRE_PASSWORD")
INHIRE_TENANT = os.getenv("INHIRE_TENANT", "frameworkdigital")


def autenticar():
    """Autentica na API Inhire"""
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
        sys.exit(1)

    return response.json().get("accessToken")


def listar_webhooks(token):
    """Lista todos os webhooks"""
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
        print(f"ERRO ao listar webhooks: {response.status_code}")
        return []

    return response.json()


def deletar_webhook(token, webhook_id):
    """Deleta um webhook"""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant": INHIRE_TENANT,
        "Content-Type": "application/json"
    }

    response = requests.delete(
        f"{INHIRE_API_URL}/integrations/webhooks/{webhook_id}",
        headers=headers
    )

    return response.status_code in [200, 204]


def main():
    print("\n" + "="*70)
    print("GERENCIADOR DE WEBHOOKS - DELETAR")
    print("="*70 + "\n")

    # Autenticar
    token = autenticar()
    print("OK Autenticado!\n")

    # Listar webhooks
    webhooks = listar_webhooks(token)

    if not webhooks:
        print("Nenhum webhook configurado.")
        return

    print(f"Total de webhooks: {len(webhooks)}\n")
    print("="*70)

    # Mostrar webhooks
    for i, wh in enumerate(webhooks, 1):
        print(f"{i}. {wh.get('name')}")
        print(f"   Evento: {wh.get('event')}")
        print(f"   URL:    {wh.get('url')[:50]}...")
        print(f"   ID:     {wh.get('id')}")
        print()

    print("="*70)
    print("\nOPCOES:")
    print("  1. Deletar todos os webhooks do Google Chat")
    print("  2. Deletar webhook especifico (escolher pelo numero)")
    print("  3. Deletar TODOS os webhooks")
    print("  0. Cancelar")
    print()

    opcao = input("Escolha uma opcao: ").strip()

    if opcao == "0":
        print("\nOperacao cancelada.")
        return

    elif opcao == "1":
        # Deletar webhooks do Google Chat
        print("\n>> Deletando webhooks do Google Chat...")
        deletados = 0

        for wh in webhooks:
            if "GChat" in wh.get('name', '') or "Google Chat" in wh.get('name', ''):
                print(f"   Deletando: {wh.get('name')}...")
                if deletar_webhook(token, wh.get('id')):
                    print(f"   OK Deletado!")
                    deletados += 1
                else:
                    print(f"   ERRO ao deletar")

        print(f"\nTotal deletado: {deletados} webhooks")

    elif opcao == "2":
        # Deletar webhook específico
        num = input("\nDigite o numero do webhook (1-{}): ".format(len(webhooks))).strip()

        try:
            idx = int(num) - 1
            if 0 <= idx < len(webhooks):
                wh = webhooks[idx]
                print(f"\n>> Deletando: {wh.get('name')}...")

                if deletar_webhook(token, wh.get('id')):
                    print(f"OK Webhook deletado com sucesso!")
                else:
                    print(f"ERRO ao deletar webhook")
            else:
                print("Numero invalido!")
        except ValueError:
            print("Entrada invalida!")

    elif opcao == "3":
        # Deletar TODOS
        confirmacao = input("\nTem certeza que deseja deletar TODOS os webhooks? (digite SIM): ").strip()

        if confirmacao.upper() == "SIM":
            print("\n>> Deletando TODOS os webhooks...")
            deletados = 0

            for wh in webhooks:
                print(f"   Deletando: {wh.get('name')}...")
                if deletar_webhook(token, wh.get('id')):
                    print(f"   OK Deletado!")
                    deletados += 1
                else:
                    print(f"   ERRO ao deletar")

            print(f"\nTotal deletado: {deletados}/{len(webhooks)} webhooks")
        else:
            print("\nOperacao cancelada (confirmacao incorreta).")

    else:
        print("\nOpcao invalida!")

    print("\n" + "="*70)


if __name__ == "__main__":
    main()
