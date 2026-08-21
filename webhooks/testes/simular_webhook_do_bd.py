"""
Simulador de Webhook usando dados REAIS do Banco de Dados
===========================================================

Busca dados REAIS do PostgreSQL e simula webhooks da Inhire
Mostra exatamente o que seria capturado e oportunidades de automação
"""

import os
import sys
import csv
import json
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# ========================================
# CONFIGURAÇÃO
# ========================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'inhire',
    'user': 'postgres',
    'password': 'postgres'  # Ajustar se necessário
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "webhook_simulation_bd")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def linha(char="=", tamanho=70):
    print(char * tamanho)


def titulo(texto):
    linha()
    print(texto)
    linha()
    print()


# ========================================
# PROCESSADORES DE WEBHOOK
# ========================================

def processar_candidatura(payload):
    """Processa candidatura (mesmo formato do Apps Script)"""
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
    """Processa mudança de etapa"""
    return [
        payload.get("changedAt", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        payload.get("jobName", ""),
        payload.get("talentName", ""),
        payload.get("previousStatus", ""),
        payload.get("newStatus", ""),
        payload.get("notes", ""),
        payload.get("userName", "Sistema")
    ]


def processar_nova_vaga(payload):
    """Processa nova vaga"""
    descricao = payload.get("description", "")
    if descricao and len(descricao) > 200:
        descricao = descricao[:200] + "..."

    return [
        payload.get("createdAt", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        payload.get("jobName", ""),
        payload.get("jobId", ""),
        descricao,
        payload.get("status", ""),
        payload.get("company", "")
    ]


def processar_requisicao(payload):
    """Processa requisição"""
    return [
        payload.get("requestedAt", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        payload.get("title", ""),
        payload.get("description", ""),
        payload.get("status", ""),
        payload.get("approvalWorkflow", "")
    ]


# ========================================
# QUERIES DO BANCO DE DADOS
# ========================================

def conectar_bd():
    """Conecta ao PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"ERRO ao conectar no BD: {e}")
        return None


def buscar_candidaturas_recentes(conn, limit=20):
    """Busca últimas candidaturas do BD"""
    query = """
    SELECT
        c.id as candidatura_id,
        c.created_at,
        c.talent_inhire_id,
        c.talent_name,
        c.vaga_id,
        c.source,
        c.custom_fields,
        v.name as vaga_nome,
        v.inhire_id as vaga_inhire_id,
        t.linkedin_username,
        t.location as location,
        t.target_salary as target_salary
    FROM candidaturas c
    LEFT JOIN vagas v ON c.vaga_id = v.id
    LEFT JOIN talentos t ON c.talent_inhire_id = t.inhire_id
    ORDER BY c.created_at DESC
    LIMIT %s
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (limit,))
        return cur.fetchall()


def buscar_mudancas_etapa_recentes(conn, limit=20):
    """Busca últimas mudanças de etapa (position timeline)"""
    query = """
    SELECT
        pt.id,
        pt.changed_at,
        pt.previous_status,
        pt.new_status,
        pt.notes,
        p.id as posicao_id,
        p.inhire_id as posicao_inhire_id,
        v.name as vaga_nome,
        v.id as vaga_id
    FROM position_timeline pt
    LEFT JOIN posicoes p ON pt.posicao_id = p.id
    LEFT JOIN vagas v ON p.vaga_id = v.id
    WHERE pt.new_status IS NOT NULL
    ORDER BY pt.changed_at DESC
    LIMIT %s
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (limit,))
        return cur.fetchall()


def buscar_vagas_recentes(conn, limit=10):
    """Busca vagas criadas recentemente"""
    query = """
    SELECT
        id,
        inhire_id,
        name,
        description,
        status,
        created_at,
        tenant_client_id,
        custom_fields
    FROM vagas
    WHERE created_at IS NOT NULL
    ORDER BY created_at DESC
    LIMIT %s
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (limit,))
        return cur.fetchall()


def buscar_requisicoes_recentes(conn, limit=10):
    """Busca requisições recentes"""
    query = """
    SELECT
        id,
        inhire_id,
        name as titulo,
        description,
        status,
        requested_at,
        approval_workflow
    FROM requisicoes
    WHERE requested_at IS NOT NULL
    ORDER BY requested_at DESC
    LIMIT %s
    """

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (limit,))
        return cur.fetchall()


# ========================================
# CONVERSORES: BD → Webhook Payload
# ========================================

def converter_candidatura_para_payload(cand):
    """Converte registro do BD para payload de webhook"""
    return {
        "tenantId": "frameworkdigital",
        "jobId": str(cand.get('vaga_inhire_id', '')),
        "jobName": cand.get('vaga_nome', ''),
        "talentId": str(cand.get('talent_inhire_id', '')),
        "talentName": cand.get('talent_name', ''),
        "stageName": "Triagem",  # Etapa inicial padrão
        "source": cand.get('source', ''),
        "linkedinUsername": cand.get('linkedin_username', ''),
        "location": cand.get('location', ''),
        "targetSalary": str(cand.get('target_salary', '')),
        "workModel": "remote",  # Exemplo
        "userName": "Sistema",
        "createdAt": str(cand.get('created_at', ''))
    }


def converter_mudanca_etapa_para_payload(mudanca):
    """Converte mudança de etapa para payload de webhook"""
    return {
        "tenantId": "frameworkdigital",
        "jobId": str(mudanca.get('posicao_inhire_id', '')),
        "jobName": mudanca.get('vaga_nome', ''),
        "talentName": f"Posição {mudanca.get('posicao_id', '')}",
        "previousStatus": mudanca.get('previous_status', ''),
        "newStatus": mudanca.get('new_status', ''),
        "changedAt": str(mudanca.get('changed_at', '')),
        "notes": mudanca.get('notes', ''),
        "userName": "Sistema"
    }


def converter_vaga_para_payload(vaga):
    """Converte vaga para payload de webhook"""
    custom_fields = vaga.get('custom_fields') or {}

    return {
        "tenantId": "frameworkdigital",
        "jobId": str(vaga.get('inhire_id', '')),
        "jobName": vaga.get('name', ''),
        "description": vaga.get('description', ''),
        "status": vaga.get('status', ''),
        "createdAt": str(vaga.get('created_at', '')),
        "company": custom_fields.get('empresa', '') if isinstance(custom_fields, dict) else '',
        "userName": "Sistema"
    }


def converter_requisicao_para_payload(req):
    """Converte requisição para payload de webhook"""
    approval = req.get('approval_workflow') or {}

    return {
        "tenantId": "frameworkdigital",
        "requisitionId": str(req.get('inhire_id', '')),
        "title": req.get('titulo', ''),
        "description": req.get('description', ''),
        "status": req.get('status', ''),
        "requestedAt": str(req.get('requested_at', '')),
        "approvalWorkflow": approval.get('name', '') if isinstance(approval, dict) else '',
        "userName": "Sistema"
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

    print(f"OK: Arquivo criado: {nome_arquivo}")
    print(f"    Linhas: {len(linhas)}")
    return caminho


def salvar_payload_json(nome_arquivo, payloads):
    """Salva payloads em JSON para análise"""
    caminho = os.path.join(OUTPUT_DIR, nome_arquivo)

    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(payloads, f, indent=2, ensure_ascii=False, default=str)

    print(f"OK: JSON salvo: {nome_arquivo}")


# ========================================
# SIMULADOR PRINCIPAL
# ========================================

def main():
    # Configurar encoding para Windows
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout.reconfigure(encoding='utf-8')

    print()
    titulo("SIMULADOR DE WEBHOOKS - DADOS REAIS DO BANCO DE DADOS")

    print("Este simulador vai:")
    print("1. Conectar no PostgreSQL local (banco 'inhire')")
    print("2. Buscar dados REAIS já sincronizados")
    print("3. Converter para formato de WEBHOOK PAYLOAD")
    print("4. Processar com a MESMA LÓGICA do Apps Script")
    print("5. Gerar CSVs + JSONs para análise de automações")
    print()

    linha()
    print()

    # Conectar BD
    print("Conectando ao banco de dados...")
    conn = conectar_bd()

    if not conn:
        print("ERRO: Falha ao conectar. Verifique se PostgreSQL esta rodando.")
        return

    print("OK: Conectado ao PostgreSQL (banco: inhire)")
    print()

    # ========================================
    # WEBHOOK 1: CANDIDATURAS
    # ========================================

    titulo("WEBHOOK 1: CANDIDATURAS (JOB_TALENT_ADDED)")

    candidaturas = buscar_candidaturas_recentes(conn, limit=20)
    print(f"Candidaturas encontradas no BD: {len(candidaturas)}")

    if candidaturas:
        # Converter para payloads
        payloads = [converter_candidatura_para_payload(c) for c in candidaturas]

        # Processar
        linhas = [processar_candidatura(p) for p in payloads]

        # Exibir exemplo
        print()
        print("EXEMPLO DE DADOS REAIS:")
        linha("-")
        if linhas:
            exemplo = linhas[0]
            payload_exemplo = payloads[0]
            colunas = [
                "Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa Inicial",
                "Origem", "LinkedIn", "Localização", "Pretensão Salarial",
                "Modelo de Trabalho", "Usuário"
            ]
            for col, val in zip(colunas, exemplo):
                print(f"  {col:25s} | {val}")
        linha("-")
        print()

        # Salvar CSV
        colunas_cand = [
            "Data/Hora", "Vaga", "Vaga ID", "Candidato ID", "Etapa Inicial",
            "Origem", "LinkedIn", "Localização", "Pretensão Salarial",
            "Modelo de Trabalho", "Usuário"
        ]
        gerar_csv("candidaturas_webhook.csv", colunas_cand, linhas)

        # Salvar JSON dos payloads
        salvar_payload_json("candidaturas_payloads.json", payloads)
        print()

    # ========================================
    # WEBHOOK 2: MUDANÇAS DE ETAPA
    # ========================================

    titulo("WEBHOOK 2: MUDANCAS DE ETAPA (POSITION_TIMELINE)")

    mudancas = buscar_mudancas_etapa_recentes(conn, limit=20)
    print(f"Mudancas de etapa encontradas: {len(mudancas)}")

    if mudancas:
        # Converter para payloads
        payloads = [converter_mudanca_etapa_para_payload(m) for m in mudancas]

        # Processar
        linhas = [processar_mudanca_etapa(p) for p in payloads]

        # Exibir exemplo
        print()
        print("EXEMPLO DE MUDANCA DE ETAPA:")
        linha("-")
        if linhas and payloads:
            exemplo = linhas[0]
            print(f"  Vaga: {payloads[0].get('jobName')}")
            print(f"  De: {payloads[0].get('previousStatus')} → Para: {payloads[0].get('newStatus')}")
            print(f"  Data: {payloads[0].get('changedAt')}")
            print(f"  Notas: {payloads[0].get('notes', 'N/A')}")
        linha("-")
        print()

        # Salvar
        colunas_mudancas = [
            "Data/Hora", "Vaga", "Candidato", "Status Anterior",
            "Novo Status", "Notas", "Usuário"
        ]
        gerar_csv("mudancas_etapa_webhook.csv", colunas_mudancas, linhas)
        salvar_payload_json("mudancas_etapa_payloads.json", payloads)
        print()

    # ========================================
    # WEBHOOK 3: VAGAS
    # ========================================

    titulo("WEBHOOK 3: NOVAS VAGAS (JOB_ADDED)")

    vagas = buscar_vagas_recentes(conn, limit=10)
    print(f"Vagas encontradas: {len(vagas)}")

    if vagas:
        payloads = [converter_vaga_para_payload(v) for v in vagas]
        linhas = [processar_nova_vaga(p) for p in payloads]

        colunas_vagas = [
            "Data/Hora", "Nome da Vaga", "Vaga ID", "Descrição", "Status", "Empresa"
        ]
        gerar_csv("vagas_webhook.csv", colunas_vagas, linhas)
        salvar_payload_json("vagas_payloads.json", payloads)
        print()

    # ========================================
    # WEBHOOK 4: REQUISIÇÕES
    # ========================================

    titulo("WEBHOOK 4: REQUISICOES (REQUISITION_STATUS_UPDATED)")

    requisicoes = buscar_requisicoes_recentes(conn, limit=10)
    print(f"Requisicoes encontradas: {len(requisicoes)}")

    if requisicoes:
        payloads = [converter_requisicao_para_payload(r) for r in requisicoes]
        linhas = [processar_requisicao(p) for p in payloads]

        colunas_reqs = [
            "Data/Hora", "Título", "Descrição", "Status", "Workflow de Aprovação"
        ]
        gerar_csv("requisicoes_webhook.csv", colunas_reqs, linhas)
        salvar_payload_json("requisicoes_payloads.json", payloads)
        print()

    # Fechar conexão
    conn.close()

    # ========================================
    # RESUMO E OPORTUNIDADES DE AUTOMAÇÃO
    # ========================================

    titulo("RESUMO DA SIMULACAO")

    print(f"Arquivos gerados em: {OUTPUT_DIR}")
    print()
    print("CSVs criados:")
    print("  1. candidaturas_webhook.csv")
    print("  2. mudancas_etapa_webhook.csv")
    print("  3. vagas_webhook.csv")
    print("  4. requisicoes_webhook.csv")
    print()
    print("JSONs de payloads:")
    print("  1. candidaturas_payloads.json")
    print("  2. mudancas_etapa_payloads.json")
    print("  3. vagas_payloads.json")
    print("  4. requisicoes_payloads.json")
    print()

    linha()
    print("OPORTUNIDADES DE AUTOMACAO IDENTIFICADAS:")
    linha()
    print()
    print("1. NOTIFICACOES AUTOMATICAS")
    print("   - Enviar email quando candidato chega em 'Proposta'")
    print("   - Alertar quando vaga recebe >10 candidaturas em 1 dia")
    print("   - Notificar quando requisicao e aprovada")
    print()
    print("2. DASHBOARDS EM TEMPO REAL")
    print("   - Grafico de candidaturas por dia (atualiza a cada 5s)")
    print("   - Conversao por etapa (live)")
    print("   - Origem mais efetiva (tempo real)")
    print()
    print("3. ACOES AUTOMATICAS")
    print("   - Enviar teste tecnico ao chegar em 'Teste Tecnico'")
    print("   - Criar task no Asana quando vaga e criada")
    print("   - Atualizar planilha de budget quando requisicao aprovada")
    print()
    print("4. ALERTAS DE SLA")
    print("   - Alertar se candidato parado >3 dias em uma etapa")
    print("   - Notificar se vaga sem candidatos ha >7 dias")
    print("   - Avisar se requisicao pendente >2 dias")
    print()
    print("5. ANALYTICS AVANCADO")
    print("   - Tempo medio por etapa (calculado em tempo real)")
    print("   - Taxa de conversao por origem")
    print("   - Performance por recrutador")
    print()

    linha()
    print()
    print("Proximos passos:")
    print("1. Abra os CSVs e JSONs gerados")
    print("2. Analise os dados REAIS capturados")
    print("3. Escolha quais automações implementar")
    print("4. Configure webhooks e Google Apps Script")
    print()
    linha()


if __name__ == "__main__":
    main()
