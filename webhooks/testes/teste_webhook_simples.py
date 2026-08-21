"""
Teste Simplificado de Webhook - Dados Reais
============================================

Versão simplificada que busca dados básicos do BD e mostra
exatamente o que os webhooks capturam
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

# Config BD
DB = {
    'host': 'localhost',
    'port': 5432,
    'database': 'inhire',
    'user': 'postgres',
    'password': 'postgres'
}

print("="*70)
print("TESTE DE WEBHOOKS - DADOS REAIS DO BANCO")
print("="*70)
print()

try:
    # Conectar
    print("Conectando ao PostgreSQL...")
    conn = psycopg2.connect(**DB)
    print("OK: Conectado!")
    print()

    # ========================================
    # WEBHOOK 1: CANDIDATURAS
    # ========================================

    print("-"*70)
    print("WEBHOOK 1: CANDIDATURAS (JOB_TALENT_ADDED)")
    print("-"*70)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                id,
                created_at,
                talent_inhire_id,
                talent_name,
                vaga_id,
                source,
                updated_at
            FROM candidaturas
            ORDER BY created_at DESC
            LIMIT 5
        """)

        candidaturas = cur.fetchall()
        print(f"Total encontrado: {len(candidaturas)} candidaturas recentes")
        print()

        if candidaturas:
            print("EXEMPLO DE PAYLOAD QUE WEBHOOK ENVIA:")
            print("-"*70)

            # Simular payload de webhook
            exemplo = candidaturas[0]
            payload_webhook = {
                "event": "JOB_TALENT_ADDED",
                "timestamp": str(exemplo['created_at']),
                "data": {
                    "candidaturaId": str(exemplo['id']),
                    "talentId": str(exemplo['talent_inhire_id']),
                    "talentName": exemplo['talent_name'],
                    "vagaId": str(exemplo['vaga_id']),
                    "source": exemplo['source'],
                    "createdAt": str(exemplo['created_at'])
                }
            }

            print(json.dumps(payload_webhook, indent=2, default=str, ensure_ascii=False))
            print()

            print("O QUE VOCE PODERIA AUTOMATIZAR:")
            print("  - Enviar email de boas-vindas ao candidato")
            print("  - Notificar recrutador via Slack/Teams")
            print("  - Adicionar em planilha Google Sheets (tempo real)")
            print("  - Criar tarefa no Asana/Trello")
            print("  - Atualizar dashboard de metricas")
            print()

    # ========================================
    # WEBHOOK 2: MUDANCAS DE ETAPA
    # ========================================

    print("-"*70)
    print("WEBHOOK 2: MUDANCAS DE ETAPA (POSITION_TIMELINE)")
    print("-"*70)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                id,
                posicao_id,
                previous_status,
                new_status,
                changed_at,
                notes
            FROM position_timeline
            WHERE new_status IS NOT NULL
            ORDER BY changed_at DESC
            LIMIT 5
        """)

        mudancas = cur.fetchall()
        print(f"Total encontrado: {len(mudancas)} mudancas de etapa")
        print()

        if mudancas:
            print("EXEMPLO DE PAYLOAD QUE WEBHOOK ENVIA:")
            print("-"*70)

            exemplo = mudancas[0]
            payload_webhook = {
                "event": "JOB_TALENT_STAGE_CHANGED",
                "timestamp": str(exemplo['changed_at']),
                "data": {
                    "posicaoId": str(exemplo['posicao_id']),
                    "previousStatus": exemplo['previous_status'],
                    "newStatus": exemplo['new_status'],
                    "notes": exemplo['notes'],
                    "changedAt": str(exemplo['changed_at'])
                }
            }

            print(json.dumps(payload_webhook, indent=2, default=str, ensure_ascii=False))
            print()

            print("O QUE VOCE PODERIA AUTOMATIZAR:")
            print("  - Enviar teste tecnico se chegou em 'Teste Tecnico'")
            print("  - Alertar se candidato parado >3 dias na mesma etapa")
            print("  - Notificar gestor se chegou em 'Proposta'")
            print("  - Calcular tempo medio por etapa (tempo real)")
            print("  - Atualizar funil de conversao automaticamente")
            print()

    # ========================================
    # WEBHOOK 3: VAGAS
    # ========================================

    print("-"*70)
    print("WEBHOOK 3: NOVAS VAGAS (JOB_ADDED)")
    print("-"*70)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                id,
                inhire_id,
                name,
                status,
                created_at,
                custom_fields
            FROM vagas
            ORDER BY created_at DESC
            LIMIT 5
        """)

        vagas = cur.fetchall()
        print(f"Total encontrado: {len(vagas)} vagas")
        print()

        if vagas:
            print("EXEMPLO DE PAYLOAD QUE WEBHOOK ENVIA:")
            print("-"*70)

            exemplo = vagas[0]
            payload_webhook = {
                "event": "JOB_ADDED",
                "timestamp": str(exemplo['created_at']),
                "data": {
                    "jobId": str(exemplo['inhire_id']),
                    "jobName": exemplo['name'],
                    "status": exemplo['status'],
                    "customFields": exemplo['custom_fields'],
                    "createdAt": str(exemplo['created_at'])
                }
            }

            print(json.dumps(payload_webhook, indent=2, default=str, ensure_ascii=False))
            print()

            print("O QUE VOCE PODERIA AUTOMATIZAR:")
            print("  - Publicar automaticamente no LinkedIn/Indeed")
            print("  - Criar card no Trello para acompanhamento")
            print("  - Notificar equipe de recrutamento")
            print("  - Atualizar planilha de budget/forecast")
            print("  - Enviar para ATS/sistema externo")
            print()

    # ========================================
    # WEBHOOK 4: REQUISICOES
    # ========================================

    print("-"*70)
    print("WEBHOOK 4: REQUISICOES (REQUISITION_STATUS_UPDATED)")
    print("-"*70)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                id,
                inhire_id,
                name,
                status,
                requested_at,
                approval_workflow
            FROM requisicoes
            WHERE requested_at IS NOT NULL
            ORDER BY requested_at DESC
            LIMIT 5
        """)

        requisicoes = cur.fetchall()
        print(f"Total encontrado: {len(requisicoes)} requisicoes")
        print()

        if requisicoes:
            print("EXEMPLO DE PAYLOAD QUE WEBHOOK ENVIA:")
            print("-"*70)

            exemplo = requisicoes[0]
            payload_webhook = {
                "event": "REQUISITION_STATUS_UPDATED",
                "timestamp": str(exemplo['requested_at']),
                "data": {
                    "requisitionId": str(exemplo['inhire_id']),
                    "title": exemplo['name'],
                    "status": exemplo['status'],
                    "approvalWorkflow": exemplo['approval_workflow'],
                    "requestedAt": str(exemplo['requested_at'])
                }
            }

            print(json.dumps(payload_webhook, indent=2, default=str, ensure_ascii=False))
            print()

            print("O QUE VOCE PODERIA AUTOMATIZAR:")
            print("  - Notificar aprovador quando requisicao criada")
            print("  - Enviar email quando aprovada/rejeitada")
            print("  - Atualizar planilha de orcamento")
            print("  - Criar vaga automaticamente se aprovada")
            print("  - Alertar se pendente >2 dias")
            print()

    # ========================================
    # RESUMO GERAL
    # ========================================

    print("="*70)
    print("RESUMO: O QUE OS WEBHOOKS PERMITEM")
    print("="*70)
    print()
    print("1. LATENCIA: ~5 segundos vs 6-12 horas (sync atual)")
    print()
    print("2. AUTOMACOES POSSÍVEIS:")
    print("   - Notificacoes instantaneas (email, Slack, Teams)")
    print("   - Dashboards em tempo real (Google Sheets, Data Studio)")
    print("   - Acoes automaticas (enviar teste, criar tarefa, etc)")
    print("   - Alertas de SLA (candidato parado, requisicao pendente)")
    print("   - Integracao com outros sistemas (ATS, CRM, etc)")
    print()
    print("3. BENEFICIOS:")
    print("   - Custo: R$ 0 (vs R$ 100-200/mes atual)")
    print("   - Sem servidor (Google Apps Script e gratuito)")
    print("   - Setup: 15-20 minutos")
    print("   - Manutencao: Minima")
    print()
    print("4. PROXIMO PASSO:")
    print("   - Escolher quais automacoes implementar")
    print("   - Configurar webhooks na Inhire")
    print("   - Criar Google Apps Script para processar")
    print()
    print("="*70)

    conn.close()

except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
