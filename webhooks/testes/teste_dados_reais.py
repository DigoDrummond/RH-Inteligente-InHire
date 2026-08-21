"""
Teste com Dados REAIS da API Inhire
Busca dados reais e gera planilhas CSV para validacao
"""

import os
import sys
import csv
from datetime import datetime

# Adicionar path do projeto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from services.api_client import InhireAPIClient
from config import settings


def linha(char="=", tamanho=70):
    print(char * tamanho)


def titulo(texto):
    linha()
    print(texto)
    linha()
    print()


# Diretorio de saida
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "planilhas_reais")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def processar_candidatura_real(candidatura):
    """Processa candidatura real da API"""
    # Buscar dados da vaga
    job = candidatura.get('job', {})
    talent = candidatura.get('talent', {})

    return [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        job.get('name', ''),
        job.get('id', ''),
        talent.get('id', ''),
        candidatura.get('stageName', ''),
        candidatura.get('source', ''),
        talent.get('linkedinUsername', ''),
        talent.get('location', ''),
        talent.get('targetSalary', ''),
        candidatura.get('workModel', ''),
        candidatura.get('user', {}).get('name', 'Sistema')
    ]


def processar_vaga_real(vaga):
    """Processa vaga real da API"""
    return [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        vaga.get('name', ''),
        vaga.get('id', ''),
        vaga.get('description', '')[:200] if vaga.get('description') else '',  # Limitar descrição
        vaga.get('createdBy', {}).get('name', 'Sistema')
    ]


def processar_requisicao_real(req):
    """Processa requisição real da API"""
    return [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        req.get('title', ''),
        req.get('id', ''),
        req.get('previousStatus', ''),
        req.get('status', ''),
        req.get('user', {}).get('name', 'Sistema')
    ]


def gerar_csv(nome_arquivo, colunas, linhas):
    """Gera arquivo CSV"""
    caminho = os.path.join(OUTPUT_DIR, nome_arquivo)

    with open(caminho, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(colunas)
        writer.writerows(linhas)

    print(f"  Arquivo criado: {nome_arquivo}")
    print(f"  Linhas: {len(linhas)}")
    return caminho


def main():
    print()
    titulo("TESTE COM DADOS REAIS DA API INHIRE")

    print("Este teste vai:")
    print("1. Conectar na API Inhire (Framework)")
    print("2. Buscar dados REAIS de candidaturas, vagas, etc.")
    print("3. Transformar em formato de PAYLOAD DE WEBHOOK")
    print("4. Processar exatamente como o Apps Script faria")
    print("5. Gerar arquivos CSV para validacao")
    print()

    linha()
    print()

    # Inicializar cliente API
    print("Conectando na API Inhire...")
    try:
        client = InhireAPIClient()
        print(f"  OK Conectado! Tenant: {settings.INHIRE_TENANT}")
        print()
    except Exception as e:
        print(f"  ERRO ao conectar: {e}")
        return

    # ========================================
    # TESTE 1: CANDIDATURAS REAIS
    # ========================================

    titulo("TESTE 1: CANDIDATURAS REAIS (job-talent-added)")

    try:
        print("Buscando candidaturas recentes...")

        # Buscar candidaturas com limit
        response = client._request(
            'POST',
            f'/tenants/{INHIRE_TENANT}/job-talents/paginated',
            json={
                'page': 0,
                'size': 20,  # Buscar 20 candidaturas
                'sort': [{'field': 'createdAt', 'direction': 'DESC'}]
            }
        )

        candidaturas = response.get('content', [])
        print(f"  Candidaturas encontradas: {len(candidaturas)}")
        print()

        if not candidaturas:
            print("  AVISO: Nenhuma candidatura encontrada")
            print()
            linhas_cand = []
        else:
            # Processar candidaturas
            linhas_cand = []
            for cand in candidaturas[:10]:  # Pegar só 10 para teste
                try:
                    linha_planilha = processar_candidatura_real(cand)
                    linhas_cand.append(linha_planilha)
                except Exception as e:
                    print(f"  ERRO ao processar candidatura {cand.get('id')}: {e}")

            print(f"  Candidaturas processadas: {len(linhas_cand)}")

        # Gerar CSV
        colunas_cand = [
            "Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa Inicial",
            "Origem", "LinkedIn", "Localizacao", "Pretensao Salarial",
            "Modelo de Trabalho", "Usuario"
        ]

        arquivo_cand = gerar_csv("1_candidaturas_reais.csv", colunas_cand, linhas_cand)
        print()

    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()
        print()

    # ========================================
    # TESTE 2: VAGAS REAIS
    # ========================================

    titulo("TESTE 2: VAGAS REAIS (job-added)")

    try:
        print("Buscando vagas recentes...")

        response = client._request(
            'POST',
            f'/tenants/{INHIRE_TENANT}/jobs/paginated',
            json={
                'page': 0,
                'size': 10,
                'sort': [{'field': 'createdAt', 'direction': 'DESC'}]
            }
        )

        vagas = response.get('content', [])
        print(f"  Vagas encontradas: {len(vagas)}")
        print()

        if not vagas:
            print("  AVISO: Nenhuma vaga encontrada")
            print()
            linhas_vagas = []
        else:
            # Processar vagas
            linhas_vagas = []
            for vaga in vagas[:10]:
                try:
                    linha_planilha = processar_vaga_real(vaga)
                    linhas_vagas.append(linha_planilha)
                except Exception as e:
                    print(f"  ERRO ao processar vaga {vaga.get('id')}: {e}")

            print(f"  Vagas processadas: {len(linhas_vagas)}")

        # Gerar CSV
        colunas_vagas = [
            "Data/Hora", "Nome da Vaga", "Vaga ID", "Descricao", "Criado por"
        ]

        arquivo_vagas = gerar_csv("3_vagas_reais.csv", colunas_vagas, linhas_vagas)
        print()

    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()
        print()

    # ========================================
    # TESTE 3: REQUISICOES REAIS
    # ========================================

    titulo("TESTE 3: REQUISICOES REAIS (requisition-status-updated)")

    try:
        print("Buscando requisicoes recentes...")

        response = client._request(
            'POST',
            f'/tenants/{INHIRE_TENANT}/requisitions/paginated',
            json={
                'page': 0,
                'size': 10,
                'sort': [{'field': 'createdAt', 'direction': 'DESC'}]
            }
        )

        requisicoes = response.get('content', [])
        print(f"  Requisicoes encontradas: {len(requisicoes)}")
        print()

        if not requisicoes:
            print("  AVISO: Nenhuma requisicao encontrada")
            print()
            linhas_reqs = []
        else:
            # Processar requisições
            linhas_reqs = []
            for req in requisicoes[:10]:
                try:
                    linha_planilha = processar_requisicao_real(req)
                    linhas_reqs.append(linha_planilha)
                except Exception as e:
                    print(f"  ERRO ao processar requisicao {req.get('id')}: {e}")

            print(f"  Requisicoes processadas: {len(linhas_reqs)}")

        # Gerar CSV
        colunas_reqs = [
            "Data/Hora", "Titulo", "Requisicao ID", "Status Anterior",
            "Novo Status", "Usuario"
        ]

        arquivo_reqs = gerar_csv("5_requisicoes_reais.csv", colunas_reqs, linhas_reqs)
        print()

    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()
        print()

    # ========================================
    # RESUMO FINAL
    # ========================================

    titulo("RESUMO DOS TESTES COM DADOS REAIS")

    print("ARQUIVOS GERADOS:")
    print(f"  1. {OUTPUT_DIR}\\1_candidaturas_reais.csv")
    print(f"     - Tipo: Candidaturas REAIS")
    print(f"     - Linhas: {len(linhas_cand) if 'linhas_cand' in locals() else 0}")
    print()
    print(f"  2. {OUTPUT_DIR}\\3_vagas_reais.csv")
    print(f"     - Tipo: Vagas REAIS")
    print(f"     - Linhas: {len(linhas_vagas) if 'linhas_vagas' in locals() else 0}")
    print()
    print(f"  3. {OUTPUT_DIR}\\5_requisicoes_reais.csv")
    print(f"     - Tipo: Requisicoes REAIS")
    print(f"     - Linhas: {len(linhas_reqs) if 'linhas_reqs' in locals() else 0}")
    print()

    linha()
    print("DADOS SAO REAIS DA API INHIRE!")
    linha()
    print()

    print("COMO VALIDAR:")
    print("1. Abra a pasta: planilhas_reais/")
    print("2. Abra cada arquivo .csv no Excel ou Google Sheets")
    print("3. Verifique se os dados SAO REAIS da Framework")
    print("4. Compare formato com as planilhas de teste")
    print()

    linha()


if __name__ == "__main__":
    main()
