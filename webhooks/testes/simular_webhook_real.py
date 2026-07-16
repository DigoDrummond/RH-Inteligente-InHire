"""
Simulador de Webhook Real - Inhire
===================================

Simula o recebimento e processamento de webhooks REAIS
Testa toda a logica antes de subir para Apps Script

Fluxo:
1. Conecta na API Inhire
2. Busca dados REAIS (candidaturas, vagas, etc.)
3. Transforma em payloads de webhook
4. Processa exatamente como Apps Script faria
5. Gera CSV de validacao
"""

import os
import sys
import csv
import uuid
from datetime import datetime

# Adicionar path do projeto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from services.api_client import InhireAPIClient
from config import settings


# ========================================
# CONFIGURACAO (simula Apps Script)
# ========================================

# Token de teste (gere um real depois)
SECRET_TOKEN = str(uuid.uuid4())

# Diretorio de saida
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "simulacao_webhook_real")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def linha(char="=", tamanho=70):
    print(char * tamanho)


def titulo(texto):
    linha()
    print(texto)
    linha()
    print()


# ========================================
# PROCESSADORES (mesma logica do Apps Script)
# ========================================

def processar_candidatura(payload):
    """
    Processa candidatura (JOB_TALENT_ADDED)
    Logica identica ao Apps Script
    """
    return [
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


def processar_mudanca_etapa(payload):
    """
    Processa mudanca de etapa (JOB_TALENT_STAGE_ADDED)
    Logica identica ao Apps Script
    """
    return [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("talentId", ""),
        payload.get("previousStageName", ""),
        payload.get("stageName", ""),
        payload.get("stageType", ""),
        payload.get("phaseType", ""),
        payload.get("userName", "Sistema")
    ]


def processar_nova_vaga(payload):
    """
    Processa nova vaga (JOB_ADDED)
    Logica identica ao Apps Script
    """
    descricao = payload.get("jobDescription", "")
    if descricao and len(descricao) > 200:
        descricao = descricao[:200]

    return [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("jobId", ""),
        descricao,
        payload.get("userName", "Sistema")
    ]


def processar_formulario(payload):
    """
    Processa formulario (FORM_RESPONSE_ADDED)
    Logica identica ao Apps Script
    """
    acertos = payload.get("correctQuestionsCount", 0)
    total = payload.get("totalQuestions", 1)
    percentual = round((acertos / total) * 100, 1) if total > 0 else 0

    return [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobId", ""),
        payload.get("talentId", ""),
        payload.get("formType", ""),
        payload.get("title", ""),
        "Sim" if payload.get("passed") else "Não",
        acertos,
        total,
        f"{percentual}%"
    ]


def processar_requisicao(payload):
    """
    Processa requisicao (REQUISITION_STATUS_UPDATED)
    Logica identica ao Apps Script
    """
    return [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("title", ""),
        payload.get("requisitionId", ""),
        payload.get("oldStatus", ""),
        payload.get("status", ""),
        payload.get("userName", "Sistema")
    ]


# ========================================
# CONVERSORES: API → Webhook Payload
# ========================================

def converter_candidatura_para_webhook(cand):
    """
    Converte dados da API para formato de webhook payload
    """
    job = cand.get('job', {})
    talent = cand.get('talent', {})

    return {
        "tenantId": settings.INHIRE_TENANT,
        "jobId": job.get('id', ''),
        "jobName": job.get('name', ''),
        "talentId": talent.get('id', ''),
        "stageName": cand.get('stageName', ''),
        "source": cand.get('source', ''),
        "linkedinUsername": talent.get('linkedinUsername', ''),
        "location": talent.get('location', ''),
        "targetSalary": talent.get('targetSalary', ''),
        "workModel": cand.get('workModel', ''),
        "userName": cand.get('createdBy', {}).get('name', 'Sistema')
    }


def converter_vaga_para_webhook(vaga):
    """
    Converte vaga da API para formato de webhook
    """
    return {
        "tenantId": settings.INHIRE_TENANT,
        "jobId": vaga.get('id', ''),
        "jobName": vaga.get('name', ''),
        "jobDescription": vaga.get('description', ''),
        "userName": vaga.get('createdBy', {}).get('name', 'Sistema')
    }


def converter_requisicao_para_webhook(req):
    """
    Converte requisicao da API para formato de webhook
    """
    return {
        "tenantId": settings.INHIRE_TENANT,
        "requisitionId": req.get('id', ''),
        "title": req.get('title', ''),
        "oldStatus": "pending",  # Simular mudanca de status
        "status": req.get('status', ''),
        "userName": req.get('createdBy', {}).get('name', 'Sistema')
    }


# ========================================
# GERADOR DE CSVs
# ========================================

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


# ========================================
# SIMULADOR PRINCIPAL
# ========================================

def simular_webhooks_reais():
    """
    Busca dados REAIS da API e simula processamento de webhooks
    """
    print()
    titulo("SIMULADOR DE WEBHOOKS REAIS - INHIRE")

    print("Este simulador vai:")
    print("1. Conectar na API Inhire (Framework)")
    print("2. Buscar dados REAIS (ultimas candidaturas, vagas, etc.)")
    print("3. Converter para formato de WEBHOOK PAYLOAD")
    print("4. Processar com a MESMA LOGICA do Apps Script")
    print("5. Gerar CSVs identicos aos que serao criados na planilha")
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
    # WEBHOOK 1: CANDIDATURAS REAIS
    # ========================================

    titulo("WEBHOOK 1: JOB_TALENT_ADDED (Candidaturas)")

    try:
        print("Buscando candidaturas recentes da API...")

        response = client._request(
            'POST',
            f'/tenants/{settings.INHIRE_TENANT}/job-talents/paginated',
            data={
                'page': 0,
                'size': 20,
                'sort': [{'field': 'createdAt', 'direction': 'DESC'}]
            }
        )

        candidaturas_api = response.get('content', [])
        print(f"  Candidaturas encontradas na API: {len(candidaturas_api)}")
        print()

        if candidaturas_api:
            # Converter para webhooks payloads
            print("Convertendo para formato de webhook...")
            webhooks_payloads = []
            for cand in candidaturas_api[:10]:  # Pegar 10 para teste
                payload = converter_candidatura_para_webhook(cand)
                webhooks_payloads.append(payload)

            print(f"  Payloads de webhook gerados: {len(webhooks_payloads)}")
            print()

            # Processar como Apps Script faria
            print("Processando webhooks (simulando Apps Script)...")
            linhas_planilha = []
            for payload in webhooks_payloads:
                linha_planilha = processar_candidatura(payload)
                linhas_planilha.append(linha_planilha)

            print(f"  Linhas processadas: {len(linhas_planilha)}")
            print()

            # Exibir exemplo
            if linhas_planilha:
                print("EXEMPLO DE DADOS REAIS:")
                linha("-")
                exemplo = linhas_planilha[0]
                colunas = [
                    "Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa Inicial",
                    "Origem", "LinkedIn", "Localizacao", "Pretensao Salarial",
                    "Modelo de Trabalho", "Usuario"
                ]
                for col, val in zip(colunas, exemplo):
                    print(f"{col:25s} | {val}")
                linha("-")
                print()

            # Gerar CSV
            colunas_cand = [
                "Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa Inicial",
                "Origem", "LinkedIn", "Localizacao", "Pretensao Salarial",
                "Modelo de Trabalho", "Usuario"
            ]

            arquivo_cand = gerar_csv("1_candidaturas_webhook_real.csv", colunas_cand, linhas_planilha)
            print()

        else:
            print("  AVISO: Nenhuma candidatura encontrada")
            print()
            linhas_planilha = []

    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()
        print()
        linhas_planilha = []

    # ========================================
    # WEBHOOK 2: VAGAS REAIS
    # ========================================

    titulo("WEBHOOK 2: JOB_ADDED (Novas Vagas)")

    try:
        print("Buscando vagas recentes da API...")

        response = client._request(
            'POST',
            f'/tenants/{settings.INHIRE_TENANT}/jobs/paginated',
            data={
                'page': 0,
                'size': 10,
                'sort': [{'field': 'createdAt', 'direction': 'DESC'}]
            }
        )

        vagas_api = response.get('content', [])
        print(f"  Vagas encontradas na API: {len(vagas_api)}")
        print()

        if vagas_api:
            # Converter para webhook payloads
            print("Convertendo para formato de webhook...")
            webhooks_payloads = []
            for vaga in vagas_api[:10]:
                payload = converter_vaga_para_webhook(vaga)
                webhooks_payloads.append(payload)

            print(f"  Payloads de webhook gerados: {len(webhooks_payloads)}")
            print()

            # Processar
            print("Processando webhooks (simulando Apps Script)...")
            linhas_vagas = []
            for payload in webhooks_payloads:
                linha_planilha = processar_nova_vaga(payload)
                linhas_vagas.append(linha_planilha)

            print(f"  Linhas processadas: {len(linhas_vagas)}")
            print()

            # Gerar CSV
            colunas_vagas = [
                "Data/Hora", "Nome da Vaga", "Vaga ID", "Descricao", "Criado por"
            ]

            arquivo_vagas = gerar_csv("3_vagas_webhook_real.csv", colunas_vagas, linhas_vagas)
            print()

        else:
            linhas_vagas = []

    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()
        print()
        linhas_vagas = []

    # ========================================
    # WEBHOOK 3: REQUISICOES REAIS
    # ========================================

    titulo("WEBHOOK 3: REQUISITION_STATUS_UPDATED (Requisicoes)")

    try:
        print("Buscando requisicoes recentes da API...")

        response = client._request(
            'POST',
            f'/tenants/{settings.INHIRE_TENANT}/requisitions/paginated',
            data={
                'page': 0,
                'size': 10,
                'sort': [{'field': 'createdAt', 'direction': 'DESC'}]
            }
        )

        requisicoes_api = response.get('content', [])
        print(f"  Requisicoes encontradas na API: {len(requisicoes_api)}")
        print()

        if requisicoes_api:
            # Converter para webhook payloads
            print("Convertendo para formato de webhook...")
            webhooks_payloads = []
            for req in requisicoes_api[:10]:
                payload = converter_requisicao_para_webhook(req)
                webhooks_payloads.append(payload)

            print(f"  Payloads de webhook gerados: {len(webhooks_payloads)}")
            print()

            # Processar
            print("Processando webhooks (simulando Apps Script)...")
            linhas_reqs = []
            for payload in webhooks_payloads:
                linha_planilha = processar_requisicao(payload)
                linhas_reqs.append(linha_planilha)

            print(f"  Linhas processadas: {len(linhas_reqs)}")
            print()

            # Gerar CSV
            colunas_reqs = [
                "Data/Hora", "Titulo", "Requisicao ID", "Status Anterior",
                "Novo Status", "Usuario"
            ]

            arquivo_reqs = gerar_csv("5_requisicoes_webhook_real.csv", colunas_reqs, linhas_reqs)
            print()

        else:
            linhas_reqs = []

    except Exception as e:
        print(f"  ERRO: {e}")
        import traceback
        traceback.print_exc()
        print()
        linhas_reqs = []

    # ========================================
    # RESUMO FINAL
    # ========================================

    titulo("RESUMO DA SIMULACAO")

    print("ARQUIVOS GERADOS:")
    print(f"  1. {OUTPUT_DIR}/1_candidaturas_webhook_real.csv")
    print(f"     - Dados REAIS de candidaturas")
    print(f"     - Linhas: {len(linhas_planilha) if 'linhas_planilha' in locals() else 0}")
    print()
    print(f"  2. {OUTPUT_DIR}/3_vagas_webhook_real.csv")
    print(f"     - Dados REAIS de vagas")
    print(f"     - Linhas: {len(linhas_vagas) if 'linhas_vagas' in locals() else 0}")
    print()
    print(f"  3. {OUTPUT_DIR}/5_requisicoes_webhook_real.csv")
    print(f"     - Dados REAIS de requisicoes")
    print(f"     - Linhas: {len(linhas_reqs) if 'linhas_reqs' in locals() else 0}")
    print()

    linha()
    print("VALIDACAO:")
    linha()
    print("1. Abra os arquivos CSV gerados")
    print("2. Verifique se os dados SAO REAIS da Framework/Inhire")
    print("3. Compare formato com as planilhas de teste")
    print("4. Se estiver OK, prossiga para Apps Script!")
    print()

    linha()
    print("TOKEN PARA APPS SCRIPT:")
    linha()
    print(f"  {SECRET_TOKEN}")
    print()
    print("Use este token ao configurar:")
    print(f"  Authorization: Bearer {SECRET_TOKEN}")
    print()

    linha()


if __name__ == "__main__":
    simular_webhooks_reais()
