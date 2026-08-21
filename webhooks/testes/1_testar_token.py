"""
TESTE 1: Validação de Token
============================

Testa se o token está no formato correto e se a validação funciona
"""

import uuid


def gerar_token():
    """Gera um token UUID seguro"""
    token = str(uuid.uuid4())
    print("=" * 70)
    print("🔑 TOKEN GERADO:")
    print("")
    print(f"   {token}")
    print("")
    print("=" * 70)
    print("")
    print("📋 COPIE ESTE TOKEN E USE NOS TESTES SEGUINTES")
    print("")
    return token


def validar_formato_token(token):
    """Valida formato do token"""
    print("\n" + "=" * 70)
    print("🔍 VALIDANDO FORMATO DO TOKEN")
    print("=" * 70)

    problemas = []

    # 1. Verificar se não está vazio
    if not token or token.strip() == "":
        problemas.append("❌ Token está vazio")

    # 2. Verificar tamanho mínimo
    if len(token) < 20:
        problemas.append(f"⚠️  Token muito curto ({len(token)} caracteres). Recomendado: 20+")

    # 3. Verificar se não tem espaços
    if " " in token:
        problemas.append("❌ Token contém espaços (não pode!)")

    # 4. Verificar caracteres especiais problemáticos
    caracteres_proibidos = ['"', "'", "<", ">", "{", "}", "[", "]", "\\", "|"]
    for char in caracteres_proibidos:
        if char in token:
            problemas.append(f"⚠️  Token contém caractere '{char}' (pode causar problemas)")

    # 5. Verificar se é token de exemplo
    tokens_exemplo = [
        "SEU_TOKEN_AQUI",
        "abc123",
        "token123",
        "seu-token-secreto"
    ]
    if token.lower() in [t.lower() for t in tokens_exemplo]:
        problemas.append("❌ Token é um exemplo! Gere um token real.")

    # Resultado
    print("")
    if problemas:
        print("⚠️  PROBLEMAS ENCONTRADOS:")
        for p in problemas:
            print(f"   {p}")
        return False
    else:
        print("✅ Token válido!")
        print(f"   Tamanho: {len(token)} caracteres")
        print(f"   Formato: OK")
        return True


def testar_header_authorization(token):
    """Testa se o header Authorization está correto"""
    print("\n" + "=" * 70)
    print("🔍 VALIDANDO HEADER AUTHORIZATION")
    print("=" * 70)

    # Formato correto
    header_correto = f"Bearer {token}"

    print("")
    print("✅ FORMATO CORRETO:")
    print(f"   {header_correto}")
    print("")

    # Exemplos incorretos
    print("❌ FORMATOS INCORRETOS (não use):")
    print(f"   bearer {token}              (bearer minúsculo)")
    print(f"   Bearer  {token}             (dois espaços)")
    print(f"   Bearer{token}               (sem espaço)")
    print(f"   \"Bearer {token}\"          (com aspas)")
    print(f"   Token {token}               (palavra errada)")
    print("")

    return header_correto


def testar_validacao_webhook(token_config, token_webhook):
    """Simula validação de webhook"""
    print("\n" + "=" * 70)
    print("🔍 SIMULANDO VALIDAÇÃO DE WEBHOOK")
    print("=" * 70)

    print("")
    print(f"Token no código:  {token_config}")
    print(f"Token no webhook: {token_webhook}")
    print("")

    # Montar headers esperados
    expected = f"Bearer {token_config}"
    received = token_webhook

    if received == expected:
        print("✅ VALIDAÇÃO PASSOU!")
        print("   Token do webhook bate com token configurado")
        print("   Webhook seria ACEITO")
        return True
    else:
        print("❌ VALIDAÇÃO FALHOU!")
        print("")
        print("   Esperado: ", expected)
        print("   Recebido: ", received)
        print("")
        print("   Webhook seria REJEITADO com erro 401 Unauthorized")

        # Detectar problema específico
        if not received.startswith("Bearer "):
            print("")
            print("⚠️  PROBLEMA: Faltou 'Bearer ' no início")
        elif token_config not in received:
            print("")
            print("⚠️  PROBLEMA: Token está diferente")

        return False


def main():
    """Executa todos os testes"""
    print("\n")
    print("=" * 70)
    print("🧪 TESTE 1: VALIDAÇÃO DE TOKEN")
    print("=" * 70)
    print("")
    print("Este teste valida:")
    print("1. Se o token está no formato correto")
    print("2. Se o header Authorization está correto")
    print("3. Se a validação de webhook funciona")
    print("")

    # Opção 1: Gerar novo token
    print("OPÇÃO 1: Gerar novo token")
    print("-" * 70)
    resposta = input("Deseja gerar um novo token? (s/n): ").strip().lower()

    if resposta == 's':
        token = gerar_token()
        input("\nPressione ENTER para continuar...")
    else:
        # Opção 2: Testar token existente
        print("\nOPÇÃO 2: Testar token existente")
        print("-" * 70)
        token = input("Cole seu token aqui: ").strip()

    # Validar formato
    validar_formato_token(token)
    input("\nPressione ENTER para continuar...")

    # Testar header
    header_correto = testar_header_authorization(token)
    input("\nPressione ENTER para continuar...")

    # Testar validação
    print("\n" + "=" * 70)
    print("🧪 TESTE DE VALIDAÇÃO")
    print("=" * 70)
    print("")
    print("Agora vamos simular se um webhook seria aceito ou rejeitado")
    print("")

    # Teste 1: Token correto
    print("\n--- Teste 1: Token CORRETO ---")
    testar_validacao_webhook(token, f"Bearer {token}")

    # Teste 2: Token incorreto (sem Bearer)
    print("\n--- Teste 2: Token SEM 'Bearer' (ERRO) ---")
    testar_validacao_webhook(token, token)

    # Teste 3: Token incorreto (bearer minúsculo)
    print("\n--- Teste 3: bearer MINÚSCULO (ERRO) ---")
    testar_validacao_webhook(token, f"bearer {token}")

    # Teste 4: Token incorreto (dois espaços)
    print("\n--- Teste 4: DOIS ESPAÇOS (ERRO) ---")
    testar_validacao_webhook(token, f"Bearer  {token}")

    # Teste 5: Token diferente
    print("\n--- Teste 5: TOKEN DIFERENTE (ERRO) ---")
    testar_validacao_webhook(token, f"Bearer outro-token-qualquer")

    # Resumo final
    print("\n" + "=" * 70)
    print("✅ RESUMO DO TESTE")
    print("=" * 70)
    print("")
    print("📋 SEU TOKEN:")
    print(f"   {token}")
    print("")
    print("📋 HEADER PARA WEBHOOKS NA INHIRE:")
    print(f"   Nome:  Authorization")
    print(f"   Valor: {header_correto}")
    print("")
    print("📋 CONFIGURAÇÃO NO CÓDIGO (Apps Script linha 21):")
    print(f"   SECRET_TOKEN: \"{token}\",")
    print("")
    print("⚠️  IMPORTANTE: Use exatamente estes valores!")
    print("=" * 70)


if __name__ == "__main__":
    main()
