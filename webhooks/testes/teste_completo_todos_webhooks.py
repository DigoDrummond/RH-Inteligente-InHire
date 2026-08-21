"""
Teste Completo de TODOS os Webhooks
Gera planilhas CSV de teste para validacao
"""

import uuid
import json
import csv
import os
from datetime import datetime, timedelta
import random


# Token de teste
TOKEN = str(uuid.uuid4())

# Diretorio de saida
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "planilhas_teste")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def linha(char="=", tamanho=70):
    print(char * tamanho)


def titulo(texto):
    linha()
    print(texto)
    linha()
    print()


# ========================================
# PAYLOADS DE TESTE (multiplos exemplos)
# ========================================

def gerar_payloads_candidaturas(qtd=10):
    """Gera multiplos payloads de candidaturas"""
    vagas = [
        "Desenvolvedor Full Stack Senior",
        "Analista de Dados Pleno",
        "Designer UX/UI",
        "Product Manager",
        "Engenheiro DevOps"
    ]

    origens = ["career-page", "linkedin", "referral", "indeed"]
    modelos = ["remote", "hybrid", "onsite"]
    locais = ["Sao Paulo, SP", "Rio de Janeiro, RJ", "Belo Horizonte, MG", "Brasilia, DF"]

    payloads = []

    for i in range(qtd):
        payload = {
            "tenantId": "frameworkdigital",
            "jobId": f"job-{i+1:03d}-abc",
            "jobName": random.choice(vagas),
            "talentId": f"talent-{i+1:03d}-def",
            "stageName": "Triagem",
            "source": random.choice(origens),
            "linkedinUsername": f"candidato{i+1}",
            "location": random.choice(locais),
            "targetSalary": random.randint(4000, 15000),
            "workModel": random.choice(modelos),
            "userId": f"user-{random.randint(1,5)}",
            "userName": f"Recrutador {random.randint(1,5)}"
        }
        payloads.append(payload)

    return payloads


def gerar_payloads_mudancas_etapa(qtd=15):
    """Gera multiplos payloads de mudancas de etapa"""
    vagas = [
        "Desenvolvedor Full Stack Senior",
        "Analista de Dados Pleno",
        "Designer UX/UI"
    ]

    transicoes = [
        ("Triagem", "Entrevista RH"),
        ("Entrevista RH", "Teste Tecnico"),
        ("Teste Tecnico", "Entrevista Tecnica"),
        ("Entrevista Tecnica", "Proposta"),
        ("Proposta", "Contratado"),
        ("Triagem", "Reprovado"),
        ("Teste Tecnico", "Reprovado")
    ]

    payloads = []

    for i in range(qtd):
        etapa_anterior, nova_etapa = random.choice(transicoes)

        payload = {
            "tenantId": "frameworkdigital",
            "jobId": f"job-{random.randint(1,10):03d}-abc",
            "jobName": random.choice(vagas),
            "talentId": f"talent-{random.randint(1,10):03d}-def",
            "previousStageName": etapa_anterior,
            "stageName": nova_etapa,
            "stageOriginId": f"stage-{i+1:03d}",
            "stageType": "default",
            "phaseType": "screening" if "Triagem" in nova_etapa or "RH" in nova_etapa else "interview",
            "userId": f"user-{random.randint(1,5)}",
            "userName": f"Recrutador {random.randint(1,5)}"
        }
        payloads.append(payload)

    return payloads


def gerar_payloads_novas_vagas(qtd=5):
    """Gera multiplos payloads de novas vagas"""
    vagas = [
        ("Desenvolvedor Python Senior", "Vaga para desenvolvimento backend com Python/Django"),
        ("Analista de BI", "Analise de dados e dashboards com Power BI"),
        ("Scrum Master", "Facilitacao de times ageis e cerimonias"),
        ("Engenheiro de Dados", "Desenvolvimento de pipelines de dados"),
        ("QA Automation", "Automacao de testes com Selenium")
    ]

    payloads = []

    for i, (nome, desc) in enumerate(vagas):
        payload = {
            "tenantId": "frameworkdigital",
            "jobId": f"new-job-{i+1:03d}-xyz",
            "jobName": nome,
            "jobDescription": desc,
            "userId": f"user-{random.randint(1,3)}",
            "userName": f"Gestor RH {random.randint(1,3)}"
        }
        payloads.append(payload)

    return payloads


def gerar_payloads_formularios(qtd=8):
    """Gera multiplos payloads de formularios"""
    formularios = [
        "Triagem Tecnica Python",
        "Triagem Tecnica JavaScript",
        "Teste de Ingles",
        "Avaliacao Cultural",
        "Questionario de Experiencia"
    ]

    payloads = []

    for i in range(qtd):
        total_questoes = random.randint(5, 15)
        acertos = random.randint(0, total_questoes)
        passou = acertos >= (total_questoes * 0.7)

        payload = {
            "tenantId": "frameworkdigital",
            "jobId": f"job-{random.randint(1,10):03d}-abc",
            "talentId": f"talent-{random.randint(1,10):03d}-def",
            "formType": "subscription",
            "title": random.choice(formularios),
            "passed": passou,
            "correctQuestionsCount": acertos,
            "totalQuestions": total_questoes
        }
        payloads.append(payload)

    return payloads


def gerar_payloads_requisicoes(qtd=6):
    """Gera multiplos payloads de requisicoes"""
    requisicoes = [
        "Desenvolvedor Mobile React Native",
        "Analista de Marketing Digital",
        "Coordenador de Projetos",
        "Assistente Administrativo",
        "Especialista em Cloud AWS",
        "Tech Lead Backend"
    ]

    transicoes = [
        ("pending", "approved"),
        ("pending", "rejected"),
        ("approved", "canceled"),
        ("pending", "approved")
    ]

    payloads = []

    for i, titulo in enumerate(requisicoes):
        status_anterior, novo_status = random.choice(transicoes)

        payload = {
            "tenantId": "frameworkdigital",
            "requisitionId": f"req-{i+1:03d}-xyz",
            "title": titulo,
            "oldStatus": status_anterior,
            "status": novo_status,
            "userId": f"user-{random.randint(1,5)}",
            "userName": f"Gestor {random.randint(1,5)}"
        }
        payloads.append(payload)

    return payloads


# ========================================
# PROCESSADORES (mesma logica do Apps Script)
# ========================================

def processar_candidatura(payload, timestamp):
    """Processa candidatura e retorna linha"""
    return [
        timestamp.strftime("%d/%m/%Y %H:%M:%S"),
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


def processar_mudanca_etapa(payload, timestamp):
    """Processa mudanca de etapa e retorna linha"""
    return [
        timestamp.strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("talentId", ""),
        payload.get("previousStageName", ""),
        payload.get("stageName", ""),
        payload.get("stageType", ""),
        payload.get("phaseType", ""),
        payload.get("userName", "Sistema")
    ]


def processar_nova_vaga(payload, timestamp):
    """Processa nova vaga e retorna linha"""
    return [
        timestamp.strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobName", ""),
        payload.get("jobId", ""),
        payload.get("jobDescription", ""),
        payload.get("userName", "Sistema")
    ]


def processar_formulario(payload, timestamp):
    """Processa formulario e retorna linha"""
    acertos = payload.get("correctQuestionsCount", 0)
    total = payload.get("totalQuestions", 1)
    percentual = round((acertos / total) * 100, 1) if total > 0 else 0

    return [
        timestamp.strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("jobId", ""),
        payload.get("talentId", ""),
        payload.get("formType", ""),
        payload.get("title", ""),
        "Sim" if payload.get("passed") else "Nao",
        acertos,
        total,
        f"{percentual}%"
    ]


def processar_requisicao(payload, timestamp):
    """Processa requisicao e retorna linha"""
    return [
        timestamp.strftime("%d/%m/%Y %H:%M:%S"),
        payload.get("title", ""),
        payload.get("requisitionId", ""),
        payload.get("oldStatus", ""),
        payload.get("status", ""),
        payload.get("userName", "Sistema")
    ]


# ========================================
# GERACAO DE PLANILHAS CSV
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
# TESTE PRINCIPAL
# ========================================

def main():
    print()
    titulo("TESTE COMPLETO DE TODOS OS WEBHOOKS")

    print("Este teste vai:")
    print("1. Gerar payloads de exemplo para os 5 tipos de eventos")
    print("2. Processar cada payload (simular Apps Script)")
    print("3. Gerar arquivos CSV com os dados")
    print("4. Voce pode abrir os CSV no Excel/Google Sheets")
    print()

    linha()
    print()

    # Timestamp base
    base_time = datetime.now()

    # ========================================
    # TESTE 1: CANDIDATURAS
    # ========================================

    titulo("TESTE 1: CANDIDATURAS (job-talent-added)")

    payloads_cand = gerar_payloads_candidaturas(10)
    print(f"Payloads gerados: {len(payloads_cand)}")

    linhas_cand = []
    for i, payload in enumerate(payloads_cand):
        timestamp = base_time - timedelta(minutes=i*10)
        linha_planilha = processar_candidatura(payload, timestamp)
        linhas_cand.append(linha_planilha)

    colunas_cand = [
        "Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa Inicial",
        "Origem", "LinkedIn", "Localizacao", "Pretensao Salarial",
        "Modelo de Trabalho", "Usuario"
    ]

    arquivo_cand = gerar_csv("1_candidaturas.csv", colunas_cand, linhas_cand)
    print()

    # ========================================
    # TESTE 2: MUDANCAS DE ETAPA
    # ========================================

    titulo("TESTE 2: MUDANCAS DE ETAPA (job-talent-stage-added)")

    payloads_mudancas = gerar_payloads_mudancas_etapa(15)
    print(f"Payloads gerados: {len(payloads_mudancas)}")

    linhas_mudancas = []
    for i, payload in enumerate(payloads_mudancas):
        timestamp = base_time - timedelta(minutes=i*5)
        linha_planilha = processar_mudanca_etapa(payload, timestamp)
        linhas_mudancas.append(linha_planilha)

    colunas_mudancas = [
        "Data/Hora", "Vaga", "Candidato ID", "Etapa Anterior",
        "Nova Etapa", "Tipo de Etapa", "Fase", "Usuario"
    ]

    arquivo_mudancas = gerar_csv("2_mudancas_etapa.csv", colunas_mudancas, linhas_mudancas)
    print()

    # ========================================
    # TESTE 3: NOVAS VAGAS
    # ========================================

    titulo("TESTE 3: NOVAS VAGAS (job-added)")

    payloads_vagas = gerar_payloads_novas_vagas(5)
    print(f"Payloads gerados: {len(payloads_vagas)}")

    linhas_vagas = []
    for i, payload in enumerate(payloads_vagas):
        timestamp = base_time - timedelta(days=i)
        linha_planilha = processar_nova_vaga(payload, timestamp)
        linhas_vagas.append(linha_planilha)

    colunas_vagas = [
        "Data/Hora", "Nome da Vaga", "Vaga ID", "Descricao", "Criado por"
    ]

    arquivo_vagas = gerar_csv("3_novas_vagas.csv", colunas_vagas, linhas_vagas)
    print()

    # ========================================
    # TESTE 4: FORMULARIOS
    # ========================================

    titulo("TESTE 4: FORMULARIOS (form-response-added)")

    payloads_forms = gerar_payloads_formularios(8)
    print(f"Payloads gerados: {len(payloads_forms)}")

    linhas_forms = []
    for i, payload in enumerate(payloads_forms):
        timestamp = base_time - timedelta(hours=i)
        linha_planilha = processar_formulario(payload, timestamp)
        linhas_forms.append(linha_planilha)

    colunas_forms = [
        "Data/Hora", "Vaga ID", "Candidato ID", "Tipo", "Titulo",
        "Aprovado?", "Acertos", "Total", "% Acerto"
    ]

    arquivo_forms = gerar_csv("4_formularios.csv", colunas_forms, linhas_forms)
    print()

    # ========================================
    # TESTE 5: REQUISICOES
    # ========================================

    titulo("TESTE 5: REQUISICOES (requisition-status-updated)")

    payloads_reqs = gerar_payloads_requisicoes(6)
    print(f"Payloads gerados: {len(payloads_reqs)}")

    linhas_reqs = []
    for i, payload in enumerate(payloads_reqs):
        timestamp = base_time - timedelta(days=i*2)
        linha_planilha = processar_requisicao(payload, timestamp)
        linhas_reqs.append(linha_planilha)

    colunas_reqs = [
        "Data/Hora", "Titulo", "Requisicao ID", "Status Anterior",
        "Novo Status", "Usuario"
    ]

    arquivo_reqs = gerar_csv("5_requisicoes.csv", colunas_reqs, linhas_reqs)
    print()

    # ========================================
    # RESUMO FINAL
    # ========================================

    titulo("RESUMO DOS TESTES")

    print("ARQUIVOS GERADOS:")
    print(f"  1. {arquivo_cand}")
    print(f"     - Tipo: Candidaturas")
    print(f"     - Linhas: {len(linhas_cand)}")
    print()
    print(f"  2. {arquivo_mudancas}")
    print(f"     - Tipo: Mudancas de Etapa")
    print(f"     - Linhas: {len(linhas_mudancas)}")
    print()
    print(f"  3. {arquivo_vagas}")
    print(f"     - Tipo: Novas Vagas")
    print(f"     - Linhas: {len(linhas_vagas)}")
    print()
    print(f"  4. {arquivo_forms}")
    print(f"     - Tipo: Formularios")
    print(f"     - Linhas: {len(linhas_forms)}")
    print()
    print(f"  5. {arquivo_reqs}")
    print(f"     - Tipo: Requisicoes")
    print(f"     - Linhas: {len(linhas_reqs)}")
    print()

    linha()
    print("TOTAL DE EVENTOS TESTADOS:")
    total = len(linhas_cand) + len(linhas_mudancas) + len(linhas_vagas) + len(linhas_forms) + len(linhas_reqs)
    print(f"  {total} eventos")
    linha()
    print()

    print("COMO VALIDAR:")
    print("1. Abra a pasta: planilhas_teste/")
    print("2. Abra cada arquivo .csv no Excel ou Google Sheets")
    print("3. Verifique se os dados estao formatados corretamente")
    print("4. Compare com as abas que serao criadas no Google Sheets")
    print()

    print("TOKEN USADO NOS TESTES:")
    print(f"  {TOKEN}")
    print()

    linha()


if __name__ == "__main__":
    main()
