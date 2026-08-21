"""
Teste Simplificado - Webhooks Google Sheets
Versao sem emojis para compatibilidade Windows
"""

import uuid
import json
from datetime import datetime


def linha(char="=", tamanho=70):
    """Imprime linha divisoria"""
    print(char * tamanho)


def titulo(texto):
    """Imprime titulo destacado"""
    linha()
    print(texto)
    linha()
    print()


def gerar_token():
    """Gera token UUID seguro"""
    token = str(uuid.uuid4())

    titulo("TOKEN GERADO")
    print(f"   {token}")
    print()
    linha()
    print()
    print("COPIE ESTE TOKEN E GUARDE!")
    print()

    return token


def validar_token(token):
    """Valida formato do token"""
    titulo("VALIDANDO TOKEN")

    problemas = []

    if not token or token.strip() == "":
        problemas.append("Token esta vazio")

    if len(token) < 20:
        problemas.append(f"Token muito curto ({len(token)} caracteres)")

    if " " in token:
        problemas.append("Token contem espacos")

    if token.lower() in ["seu_token_aqui", "abc123", "token123"]:
        problemas.append("Token e um exemplo! Use um token real")

    if problemas:
        print("PROBLEMAS ENCONTRADOS:")
        for p in problemas:
            print(f"   - {p}")
        return False
    else:
        print("OK Token valido!")
        print(f"   Tamanho: {len(token)} caracteres")
        return True


def testar_header(token):
    """Testa header Authorization"""
    titulo("HEADER AUTHORIZATION")

    header_correto = f"Bearer {token}"

    print("FORMATO CORRETO:")
    print(f"   {header_correto}")
    print()

    print("FORMATOS INCORRETOS (nao use):")
    print(f"   bearer {token}              (minusculo)")
    print(f"   Bearer  {token}             (dois espacos)")
    print(f"   Bearer{token}               (sem espaco)")
    print()

    return header_correto


def simular_validacao(token_config, token_webhook):
    """Simula validacao de webhook"""
    titulo("SIMULANDO VALIDACAO")

    print(f"Token no codigo:  {token_config}")
    print(f"Token no webhook: {token_webhook}")
    print()

    expected = f"Bearer {token_config}"

    if token_webhook == expected:
        print("OK VALIDACAO PASSOU!")
        print("   Webhook seria ACEITO")
        return True
    else:
        print("ERRO VALIDACAO FALHOU!")
        print(f"   Esperado: {expected}")
        print(f"   Recebido: {token_webhook}")
        print("   Webhook seria REJEITADO (401)")
        return False


def testar_payload():
    """Testa processamento de payload"""
    titulo("TESTANDO PAYLOAD")

    payload = {
        "tenantId": "frameworkdigital",
        "jobId": "job-123-abc",
        "jobName": "Desenvolvedor Full Stack Senior",
        "talentId": "talent-456-def",
        "stageName": "Triagem",
        "source": "career-page",
        "linkedinUsername": "joaosilva",
        "location": "Sao Paulo, SP",
        "targetSalary": 8000,
        "workModel": "hybrid",
        "userName": "Recrutador Teste"
    }

    print("PAYLOAD RECEBIDO:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()

    # Processar
    linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("jobId", ""),
        payload.get("talentId", ""),
        payload.get("stageName", ""),
        payload.get("source", ""),
        payload.get("linkedinUsername", ""),
        payload.get("location", ""),
        payload.get("targetSalary", ""),
        payload.get("workModel", ""),
        payload.get("userName", "Sistema")
    ]

    colunas = ["Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa",
               "Origem", "LinkedIn", "Localizacao", "Pretensao", "Modelo", "Usuario"]

    print("LINHA QUE SERIA ADICIONADA NA PLANILHA:")
    linha("─")

    for col, val in zip(colunas, linha):
        print(f"{col:20s} | {val}")

    linha("─")
    print()
    print("OK Payload processado com sucesso!")

    return True


def testar_webhook_completo(token):
    """Testa fluxo completo de webhook"""
    titulo("SIMULACAO COMPLETA DE WEBHOOK")

    # Payload de teste
    payload = {
        "jobName": "Desenvolvedor Senior",
        "talentId": "talent-123",
        "stageName": "Triagem"
    }

    # Cenario 1: Token correto
    print("CENARIO 1: Token CORRETO")
    linha("-")
    auth_header = f"Bearer {token}"

    expected = f"Bearer {token}"

    print(f"Header enviado: {auth_header}")
    print(f"Header esperado: {expected}")

    if auth_header == expected:
        print("OK Autenticacao passou!")
        print("OK Payload processado!")
        print("OK Resposta: 200 OK")
        print()
        resultado1 = True
    else:
        print("ERRO Autenticacao falhou!")
        resultado1 = False

    # Cenario 2: Token incorreto
    print("CENARIO 2: Token INCORRETO")
    linha("-")
    auth_header_errado = "Bearer token-errado-123"

    print(f"Header enviado: {auth_header_errado}")
    print(f"Header esperado: {expected}")

    if auth_header_errado == expected:
        print("ERRO Deveria ter falhado!")
        resultado2 = False
    else:
        print("OK Rejeitado corretamente (401)")
        print()
        resultado2 = True

    # Cenario 3: Sem Bearer
    print("CENARIO 3: SEM 'Bearer'")
    linha("-")
    auth_header_sem_bearer = token

    print(f"Header enviado: {auth_header_sem_bearer}")
    print(f"Header esperado: {expected}")

    if auth_header_sem_bearer == expected:
        print("ERRO Deveria ter falhado!")
        resultado3 = False
    else:
        print("OK Rejeitado corretamente (401)")
        print()
        resultado3 = True

    return resultado1 and resultado2 and resultado3


def main():
    """Executa todos os testes"""
    print()
    titulo("TESTE COMPLETO - WEBHOOKS GOOGLE SHEETS")

    print("Este teste valida:")
    print("1. Geracao e validacao de token")
    print("2. Header Authorization")
    print("3. Processamento de payload")
    print("4. Simulacao de webhook completo")
    print()

    input("Pressione ENTER para iniciar...")

    # Teste 1: Gerar token
    print()
    token = gerar_token()
    input("Pressione ENTER para continuar...")

    # Teste 2: Validar token
    print()
    validou = validar_token(token)
    input("Pressione ENTER para continuar...")

    # Teste 3: Header
    print()
    header = testar_header(token)
    input("Pressione ENTER para continuar...")

    # Teste 4: Validacao
    print()
    simular_validacao(token, f"Bearer {token}")
    input("Pressione ENTER para continuar...")

    # Teste 5: Payload
    print()
    testar_payload()
    input("Pressione ENTER para continuar...")

    # Teste 6: Webhook completo
    print()
    webhook_ok = testar_webhook_completo(token)
    input("Pressione ENTER para ver resumo...")

    # Resumo
    print()
    titulo("RESUMO DOS TESTES")

    print("SEU TOKEN:")
    print(f"   {token}")
    print()

    print("HEADER PARA WEBHOOKS:")
    print(f"   Nome:  Authorization")
    print(f"   Valor: {header}")
    print()

    print("CONFIGURACAO NO CODIGO (Apps Script linha 21):")
    print(f'   SECRET_TOKEN: "{token}",')
    print()

    if validou and webhook_ok:
        linha()
        print("TODOS OS TESTES PASSARAM!")
        linha()
        print()
        print("Proximo passo: Usar este token no Apps Script")
        print()
    else:
        print("ALGUNS TESTES FALHARAM")
        print("Revise os erros acima")

    linha()


if __name__ == "__main__":
    main()
