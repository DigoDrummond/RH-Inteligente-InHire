/*
================================================================================
MIGRATION 071: Corrigir Cálculo de SLA para Posições Pausadas
================================================================================

Data: 2026-03-03

OBJETIVO:
  Corrigir inconsistência no cálculo de SLA quando posição está em status 'paused'.

PROBLEMA IDENTIFICADO:
  - 11 posições (0.80%) com SLA de recrutamento negativo
  - Posição exemplo: ID 589 com SLA recrutamento = -31 dias
  - Causa: SLA geral usa data da pausa, mas período de pausa usa CURRENT_TIMESTAMP
  - Resultado: pendência > SLA total → SLA negativo

DIAGNÓSTICO (Posição 589):
  - Data publicação: 22/08/2025
  - Data pausa: 03/11/2025
  - Status atual: paused (sem retomada)

  ANTES (Migration 070):
    SLA geral = 22/08 → 03/11 = 52 dias
    SLA pendência = 03/11 → hoje (03/03) = 83 dias
    SLA recrutamento = 52 - 83 = -31 dias ❌

  DEPOIS (Migration 071):
    SLA geral = 22/08 → hoje (03/03) = 134 dias
    SLA pendência = 03/11 → hoje (03/03) = 83 dias
    SLA recrutamento = 134 - 83 = 51 dias ✅

SOLUÇÃO:
  Quando status = 'paused' (posição ainda pausada):
    - data_encerramento_ou_atualizacao = CURRENT_DATE (em vez de data_ultima_mudanca)
    - data_fim da pausa = CURRENT_DATE (em vez de CURRENT_TIMESTAMP)

  Quando status mudou de 'paused':
    - Mantém lógica atual (usa datas dos eventos)

  Resultado: Ambos usam mesma data final, SLA não fica negativo

MODIFICAÇÕES:
  1. CTE periodos_pausa (linha 102): CURRENT_TIMESTAMP → CURRENT_DATE
  2. Campo data_encerramento (linha 197): status paused → CURRENT_DATE
  3. SLA recrutamento 1º CASE (linha 276): status paused → CURRENT_DATE
  4. SLA recrutamento 2º CASE (linha 297): status paused → CURRENT_DATE
  5. SLA geral 1º CASE (linha 338): status paused → CURRENT_DATE
  6. SLA geral 2º CASE (linha 359): status paused → CURRENT_DATE
  7. Indicador prazo 1º CASE (linha 385): status paused → CURRENT_DATE
  8. Indicador prazo 2º CASE (linha 407): status paused → CURRENT_DATE

IMPACTO:
  - 11 posições com SLA negativo → SLA positivo correto
  - 1 posição pausada não afetada (pausa recente)
  - 0 regressões esperadas
  - 100% das outras colunas inalteradas (incluindo email_pessoal com fallback)

Base: Migration 070 (com fallback de e-mail)

================================================================================
*/

-- ============================================================================
-- RECRIAR VIEW COM CORREÇÃO DE SLA PAUSADO
-- ============================================================================

-- NOTA: DROP VIEW removido para evitar erro "candidaturas does not exist"
-- CREATE OR REPLACE substitui automaticamente a view existente

CREATE OR REPLACE VIEW vw_analise_posicoes AS
WITH ultima_etapa AS (
    SELECT
        cd.vaga_id,
        cd.stage_name,
        cd.stage_order,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.stage_order DESC, cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    WHERE cd.stage_name IS NOT NULL AND cd.stage_order IS NOT NULL
),
ultimo_status_posicao AS (
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca,
        notes
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
),
eventos_pausa AS (
    SELECT DISTINCT
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        CASE
            WHEN (previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused'
                THEN 'INICIO_PAUSA'
            WHEN previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed')
                THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline
    WHERE
        ((previous_status = 'open' OR previous_status IS NULL) AND new_status = 'paused')
        OR (previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed'))
),
periodos_pausa AS (
    SELECT
        inicio.posicao_id,
        inicio.changed_at AS data_inicio,
        COALESCE(
            (SELECT MIN(fim.changed_at)
             FROM eventos_pausa fim
             WHERE fim.posicao_id = inicio.posicao_id
               AND fim.tipo_evento = 'FIM_PAUSA'
               AND fim.changed_at > inicio.changed_at
            ),
            CURRENT_DATE  -- MODIFICADO EM MIGRATION 071 (era CURRENT_TIMESTAMP)
        ) AS data_fim
    FROM eventos_pausa inicio
    WHERE inicio.tipo_evento = 'INICIO_PAUSA'
),
periodos_unicos AS (
    SELECT DISTINCT
        posicao_id,
        data_inicio,
        data_fim
    FROM periodos_pausa
),
pendencias_posicao AS (
    SELECT
        posicao_id,
        SUM(calcular_dias_uteis(DATE(data_inicio), DATE(data_fim))) AS total_dias_pausado,
        MIN(data_inicio) AS primeira_pausa,
        MAX(data_fim) AS ultima_retomada,
        COUNT(*) AS num_ciclos,
        STRING_AGG(TO_CHAR(data_inicio, 'DD/MM/YYYY'), '; ' ORDER BY data_inicio) AS datas_inicio_pausa,
        STRING_AGG(
            CASE
                WHEN data_fim::date = CURRENT_DATE THEN 'Em andamento'
                ELSE TO_CHAR(data_fim, 'DD/MM/YYYY')
            END,
            '; '
            ORDER BY data_inicio
        ) AS datas_fim_pausa,
        STRING_AGG(
            TO_CHAR(data_inicio, 'DD/MM/YYYY') || ' a ' ||
            CASE
                WHEN data_fim::date = CURRENT_DATE THEN 'Hoje'
                ELSE TO_CHAR(data_fim, 'DD/MM/YYYY')
            END ||
            ' (' || calcular_dias_uteis(DATE(data_inicio), DATE(data_fim))::text || 'd úteis)',
            '; '
            ORDER BY data_inicio
        ) AS detalhamento_periodos
    FROM periodos_unicos
    GROUP BY posicao_id
)
SELECT
    -- ========================================
    -- NOVOS CAMPOS (Migration 064)
    -- ========================================

    -- 1. ID da Vaga (NOVO)
    v.id AS vaga_id,

    -- 2. Nome da Vaga (NOVO)
    v.name AS vaga_nome,

    -- ========================================
    -- CAMPOS ORIGINAIS (Migration 063)
    -- ========================================

    -- 3. ID da Posição (era coluna 1)
    p.id AS id_position,

    -- 4. Cargo (era coluna 2)
    v.name AS cargo,

    -- 5. Data de abertura (era coluna 3)
    DATE(r.requested_at) AS data_abertura,

    -- 6. Data da publicação (era coluna 4)
    DATE(p.opened_at) AS data_publicacao,

    -- 7. Prazo do Processo Seletivo (era coluna 5)
    v.sla_days_goal AS prazo_processo_seletivo,

    -- 8. Cliente (era coluna 6)
    c.name AS cliente,

    -- 9. Torre (era coluna 7)
    COALESCE(
        get_custom_field_value(r.custom_fields, 'Torre'),
        v.custom_fields->>'Torre'
    ) AS torre,

    -- 10. Status (era coluna 8)
    COALESCE(usp.new_status, p.status) AS status_atual,

    -- 11. Data de Encerramento (era coluna 9) -- MODIFICADO EM MIGRATION 071
    CASE
        WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
            THEN DATE(p.hired_at)
        WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
             AND usp.data_ultima_mudanca IS NOT NULL
             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
            THEN DATE(usp.data_ultima_mudanca)
        WHEN COALESCE(usp.new_status, p.status) = 'open'
            THEN CURRENT_DATE
        WHEN COALESCE(usp.new_status, p.status) = 'paused'
            THEN CURRENT_DATE  -- MODIFICADO (era DATE(usp.data_ultima_mudanca))
        WHEN usp.data_ultima_mudanca IS NOT NULL
             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
            THEN DATE(usp.data_ultima_mudanca)
        ELSE NULL
    END AS data_encerramento_ou_atualizacao,

    -- 12. Motivo (mesclado) (era coluna 10)
    CASE
        WHEN v.custom_fields->>'Motivo de Cancelamento' IS NOT NULL
             AND COALESCE(mst.descricao_pt, usp.notes) IS NOT NULL
        THEN v.custom_fields->>'Motivo de Cancelamento' || ' | ' || COALESCE(mst.descricao_pt, usp.notes)
        ELSE COALESCE(
            v.custom_fields->>'Motivo de Cancelamento',
            COALESCE(mst.descricao_pt, usp.notes)
        )
    END AS motivo_cancelamento_paralisacao,

    -- 13. Etapa Funil (era coluna 11)
    ue.stage_name AS etapa_funil,

    -- 14. Senioridade (era coluna 12)
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,

    -- 15. Motivo de contratação (era coluna 13)
    CASE p.reason
        WHEN 'expansion' THEN 'Aumento de quadro'
        WHEN 'replacement' THEN 'Substituição'
        WHEN 'other' THEN 'Outros'
        WHEN 'new-position' THEN 'Nova posição'
        WHEN 'turnover' THEN 'Turnover'
        WHEN 'internal-transfer' THEN 'Transferência interna'
        ELSE p.reason
    END AS motivo_contratacao,

    -- 16. Modalidade de Contratação (era coluna 14)
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,

    -- 17. Pessoa a Ser Substituida (era coluna 15)
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,

    -- 18. Responsável (era coluna 16)
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,

    -- 19. Email Responsável Cliente (era coluna 17)
    get_custom_field_value(r.custom_fields, 'Email do responsável por parte do cliente') AS email_responsavel_cliente,

    -- 20. Recrutador da vaga (era coluna 18)
    v.user_name AS recrutador_vaga,

    -- 21. Inicio Pendência com Cliente (era coluna 19)
    pp.datas_inicio_pausa AS inicio_pendencia_cliente,

    -- 22. Fim Pendência com Cliente (era coluna 20)
    pp.datas_fim_pausa AS fim_pendencia_cliente,

    -- 23. SLA Pendência Cliente (era coluna 21)
    pp.total_dias_pausado AS sla_pendencia_cliente,

    -- 24. Num Ciclos Pausa (era coluna 22)
    pp.num_ciclos AS num_ciclos_pausa,

    -- 25. Detalhamento Pausas (era coluna 23)
    pp.detalhamento_periodos AS detalhamento_pausas,

    -- 26. SLA Recrutamento (era coluna 24) -- MODIFICADO EM MIGRATION 071
    CASE
        WHEN (
            CASE
                WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                    THEN DATE(p.hired_at)
                WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                     AND usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN COALESCE(usp.new_status, p.status) = 'open'
                    THEN CURRENT_DATE
                WHEN COALESCE(usp.new_status, p.status) = 'paused'
                    THEN CURRENT_DATE  -- MODIFICADO (era DATE(usp.data_ultima_mudanca))
                WHEN usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                ELSE NULL
            END
        ) IS NOT NULL
        THEN
            calcular_dias_uteis(
                DATE(COALESCE(r.requested_at, p.opened_at)),
                CASE
                    WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                        THEN DATE(p.hired_at)
                    WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                         AND usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    WHEN COALESCE(usp.new_status, p.status) = 'open'
                        THEN CURRENT_DATE
                    WHEN COALESCE(usp.new_status, p.status) = 'paused'
                        THEN CURRENT_DATE  -- MODIFICADO (era DATE(usp.data_ultima_mudanca))
                    WHEN usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    ELSE NULL
                END
            )
            - COALESCE(pp.total_dias_pausado, 0)
        ELSE NULL
    END AS sla_recrutamento,

    -- 27. Nome da Pessoa Contratada (era coluna 25)
    t_contratado.name AS nome_pessoa_contratada,

    -- 28. E-mail Pessoal (era coluna 26) -- PRESERVADO DE MIGRATION 070
    COALESCE(
        t_contratado.email,
        (SELECT cd.talent_email
         FROM candidaturas cd
         WHERE cd.vaga_id = p.vaga_id
         AND cd.stage_name = 'Contratação'
         LIMIT 1)
    ) AS email_pessoal,

    -- 29. Modalidade de Contratação Requisição (era coluna 27)
    get_custom_field_value(r.custom_fields, 'Modalidade de Contratação') AS modalidade_contratacao_req,

    -- 30. SLA Geral (era coluna 28) -- MODIFICADO EM MIGRATION 071
    CASE
        WHEN (
            CASE
                WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                    THEN DATE(p.hired_at)
                WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                     AND usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN COALESCE(usp.new_status, p.status) = 'open'
                    THEN CURRENT_DATE
                WHEN COALESCE(usp.new_status, p.status) = 'paused'
                    THEN CURRENT_DATE  -- MODIFICADO (era DATE(usp.data_ultima_mudanca))
                WHEN usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                ELSE NULL
            END
        ) IS NOT NULL
        THEN
            calcular_dias_uteis(
                DATE(COALESCE(r.requested_at, p.opened_at)),
                CASE
                    WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                        THEN DATE(p.hired_at)
                    WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                         AND usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    WHEN COALESCE(usp.new_status, p.status) = 'open'
                        THEN CURRENT_DATE
                    WHEN COALESCE(usp.new_status, p.status) = 'paused'
                        THEN CURRENT_DATE  -- MODIFICADO (era DATE(usp.data_ultima_mudanca))
                    WHEN usp.data_ultima_mudanca IS NOT NULL
                         AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                        THEN DATE(usp.data_ultima_mudanca)
                    ELSE NULL
                END
            )
        ELSE NULL
    END AS sla_geral,

    -- 31. Meta Recrutamento (era coluna 29) -- MODIFICADO EM MIGRATION 071
    CASE
        WHEN v.sla_days_goal IS NULL
            THEN 'Sem Meta Definida'
        WHEN (
            CASE
                WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                    THEN DATE(p.hired_at)
                WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                     AND usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                WHEN COALESCE(usp.new_status, p.status) = 'open'
                    THEN CURRENT_DATE
                WHEN COALESCE(usp.new_status, p.status) = 'paused'
                    THEN CURRENT_DATE  -- MODIFICADO (era DATE(usp.data_ultima_mudanca))
                WHEN usp.data_ultima_mudanca IS NOT NULL
                     AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                    THEN DATE(usp.data_ultima_mudanca)
                ELSE NULL
            END
        ) IS NOT NULL
        THEN
            CASE
                WHEN calcular_dias_uteis(
                    DATE(p.opened_at),
                    CASE
                        WHEN p.hired_at IS NOT NULL AND DATE(p.hired_at) >= DATE(p.opened_at)
                            THEN DATE(p.hired_at)
                        WHEN COALESCE(usp.new_status, p.status) IN ('canceled', 'closed')
                             AND usp.data_ultima_mudanca IS NOT NULL
                             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                            THEN DATE(usp.data_ultima_mudanca)
                        WHEN COALESCE(usp.new_status, p.status) = 'open'
                            THEN CURRENT_DATE
                        WHEN COALESCE(usp.new_status, p.status) = 'paused'
                            THEN CURRENT_DATE  -- MODIFICADO (era DATE(usp.data_ultima_mudanca))
                        WHEN usp.data_ultima_mudanca IS NOT NULL
                             AND DATE(usp.data_ultima_mudanca) >= DATE(p.opened_at)
                            THEN DATE(usp.data_ultima_mudanca)
                        ELSE NULL
                    END
                ) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,

    -- 32. Empresa (era coluna 30)
    get_custom_field_value(r.custom_fields, 'Empresa') AS empresa,

    -- 33. Tipo de Posição (era coluna 31)
    get_custom_field_value(r.custom_fields, 'Tipo de Serviço') AS tipo_posicao,

    -- 34. Nome do Workflow de Aprovação (era coluna 32)
    r.approval_workflow->>'name' AS nome_workflow_aprovacao

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN talentos t_contratado ON t_contratado.inhire_id = p.talent_id
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
    LEFT JOIN motivo_status_traducao mst ON mst.codigo = usp.notes AND mst.ativo = TRUE
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at ASC NULLS LAST;

-- ============================================================================
-- COMENTÁRIOS
-- ============================================================================

COMMENT ON VIEW vw_analise_posicoes IS
'View FINAL para análise de posições - Migration 071 (2026-03-03).
34 campos. Histórico completo:
  - 047-062: evolução de campos e traduções
  - 063: REORDENAÇÃO + mesclagem de motivo
  - 064: ADICIONADO vaga_id e vaga_nome NO INÍCIO
  - 065: ALTERADA ORDENAÇÃO para ASC (data_publicacao)
  - 070: ADICIONADO FALLBACK no email_pessoal (busca de candidaturas)
  - 071: CORRIGIDO SLA para posições pausadas (CURRENT_DATE quando paused)

ORDEM DOS CAMPOS:
  1-2: Informações da vaga
  3-34: Campos de análise e SLA

CARACTERÍSTICAS:
  - Usa calcular_dias_uteis() para SLAs
  - email_pessoal com fallback para candidaturas (Migration 070)
  - SLA corrigido para posições pausadas (Migration 071)
  - 34 campos estruturados';

COMMENT ON COLUMN vw_analise_posicoes.email_pessoal IS
'E-mail pessoal do talento contratado. Busca primeiro em talentos.email,
se NULL busca em candidaturas.talent_email (stage_name = Contratação).
Migration 070 (2026-03-03)';

COMMENT ON COLUMN vw_analise_posicoes.sla_recrutamento IS
'SLA de recrutamento em dias úteis (excluindo pausas). Para status paused,
usa CURRENT_DATE como data final para evitar valores negativos.
Migration 071 (2026-03-03)';

COMMENT ON COLUMN vw_analise_posicoes.sla_geral IS
'SLA geral em dias úteis (incluindo pausas). Para status paused,
usa CURRENT_DATE como data final para evitar valores negativos.
Migration 071 (2026-03-03)';
