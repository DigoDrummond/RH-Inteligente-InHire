"""
Executor de Todos os Testes
============================

Executa todos os testes em sequência
"""

import subprocess
import sys
import os


def executar_teste(numero, nome, arquivo):
    """Executa um teste específico"""
    print("\n")
    print("=" * 70)
    print(f"🧪 TESTE {numero}: {nome}")
    print("=" * 70)
    print("")

    resposta = input(f"Executar este teste? (s/n): ").strip().lower()

    if resposta != 's':
        print("⏭️  Teste pulado.")
        return None

    print(f"\n▶️  Executando {arquivo}...\n")

    try:
        # Executar script
        result = subprocess.run(
            [sys.executable, arquivo],
            check=True
        )

        if result.returncode == 0:
            print(f"\n✅ Teste {numero} concluído com sucesso!")
            return True
        else:
            print(f"\n❌ Teste {numero} falhou!")
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao executar teste: {e}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Arquivo não encontrado: {arquivo}")
        return False


def main():
    """Executa todos os testes"""
    print("\n")
    print("=" * 70)
    print("🚀 EXECUTOR DE TESTES - WEBHOOKS GOOGLE SHEETS")
    print("=" * 70)
    print("")
    print("Este script vai executar todos os testes em sequência:")
    print("")
    print("1. Teste de Token")
    print("2. Teste de Payloads")
    print("3. Teste de Webhook Completo")
    print("")

    resposta = input("Deseja prosseguir? (s/n): ").strip().lower()

    if resposta != 's':
        print("\n❌ Execução cancelada.")
        return

    # Diretório dos testes
    dir_atual = os.path.dirname(os.path.abspath(__file__))

    # Testes a executar
    testes = [
        (1, "Validação de Token", os.path.join(dir_atual, "1_testar_token.py")),
        (2, "Validação de Payloads", os.path.join(dir_atual, "2_testar_payload.py")),
        (3, "Simulação Completa", os.path.join(dir_atual, "3_testar_webhook_completo.py"))
    ]

    # Executar testes
    resultados = []
    for numero, nome, arquivo in testes:
        resultado = executar_teste(numero, nome, arquivo)
        if resultado is not None:
            resultados.append((nome, resultado))

    # Resumo final
    print("\n\n")
    print("=" * 70)
    print("📊 RESUMO GERAL DOS TESTES")
    print("=" * 70)
    print("")

    if not resultados:
        print("⚠️  Nenhum teste foi executado.")
        return

    total = len(resultados)
    passou = sum(1 for _, r in resultados if r)
    falhou = total - passou

    print(f"Total de testes executados: {total}")
    print("")

    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"   {status}: {nome}")

    print("")
    print(f"✅ Passaram: {passou}")
    print(f"❌ Falharam: {falhou}")
    print("")

    if falhou == 0:
        print("=" * 70)
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("=" * 70)
        print("")
        print("✅ Seu código está validado e pronto para Apps Script!")
        print("")
        print("📋 PRÓXIMOS PASSOS:")
        print("1. Copie o token gerado no Teste 1")
        print("2. Cole no arquivo 2_setup_planilha.js (linha 19)")
        print("3. Cole no arquivo 3_webhook_receiver.js (linha 21)")
        print("4. Prossiga com setup no Google Apps Script")
        print("")
    else:
        print("=" * 70)
        print("⚠️  ALGUNS TESTES FALHARAM")
        print("=" * 70)
        print("")
        print("Revise os erros e execute os testes novamente.")
        print("")

    print("=" * 70)


if __name__ == "__main__":
    main()
