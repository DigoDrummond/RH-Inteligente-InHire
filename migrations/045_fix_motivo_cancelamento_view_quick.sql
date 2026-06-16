/*
================================================================================
MIGRATION 045 (QUICK): Correção do Motivo de Cancelamento na vw_analise_posicoes
================================================================================

Data: 2026-03-20
Descrição:
  Versão RÁPIDA que usa CREATE OR REPLACE VIEW para corrigir apenas o campo
  motivo_cancelamento_paralisacao, buscando de position_timeline.notes

PROBLEMA:
  Migration 044 buscava: v.custom_fields->>'Motivo de Cancelamento'
  Mas o motivo está em: position_timeline.notes

CORREÇÃO:
  1. CTE motivo_cancelamento_pausa: busca notes da position_timeline
  2. LEFT JOIN na query principal
  3. Retorna notes dos eventos canceled/paused/closed

TEMPO ESTIMADO: 5-10 segundos (vs 10+ minutos da versão completa)

================================================================================
*/

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
pessoa_contratada AS (
    SELECT
        cd.vaga_id,
        cd.talent_inhire_id,
        t.name AS talent_name,
        t.email AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    INNER JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    WHERE cd.stage_name = 'Contratação' AND cd.stage_order > 9
),
ultimo_status_posicao AS (
    SELECT DISTINCT ON (posicao_id)
        posicao_id,
        new_status,
        changed_at AS data_ultima_mudanca
    FROM position_timeline
    ORDER BY posicao_id, changed_at DESC
),
motivo_cancelamento_pausa AS (
    -- ✅ NOVO: Busca motivos de cancelamento/pausa da position_timeline
    SELECT
        posicao_id,
        STRING_AGG(
            DISTINCT notes,
            '; '
            ORDER BY notes
        ) AS motivo_cancelamento
    FROM position_timeline
    WHERE new_status IN ('canceled', 'paused', 'closed')
      AND notes IS NOT NULL
      AND TRIM(notes) != ''
    GROUP BY posicao_id
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
            CURRENT_TIMESTAMP
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
        SUM(DATE(data_fim) - DATE(data_inicio)) AS total_dias_pausado,
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
            ' (' || (DATE(data_fim) - DATE(data_inicio))::text || 'd)',
            '; '
            ORDER BY data_inicio
        ) AS detalhamento_periodos
    FROM periodos_unicos
    GROUP BY posicao_id
),
source_posicao AS (
    SELECT
        p.id AS posicao_id,
        COALESCE(
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             AND cd.stage_name = 'Contratação'
             LIMIT 1),
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             GROUP BY cd.source
             ORDER BY COUNT(*) DESC
             LIMIT 1)
        ) AS source
    FROM posicoes p
)
SELECT
    -- IDENTIFICAÇÃO
    p.id AS id_position,
    v.name AS cargo,
    c.name AS cliente,
    v.custom_fields->>'Torre' AS torre,

    -- DATAS PRINCIPAIS
    DATE(r.requested_at) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,

    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
        THEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at))
        ELSE NULL
    END AS data_encerramento_ou_atualizacao,

    -- STATUS E CONTEXTO
    COALESCE(usp.new_status, p.status) AS status_atual,

    -- ✅ CORRIGIDO (migration 045): Busca de position_timeline.notes (não custom_fields)
    mcp.motivo_cancelamento AS motivo_cancelamento_paralisacao,

    ue.stage_name AS etapa_funil,

    -- PERFIL DA VAGA
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,

    -- RESPONSÁVEIS
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,
    v.user_name AS recrutador_vaga,

    -- PAUSAS E PENDÊNCIAS
    pp.datas_inicio_pausa AS inicio_pendencia_cliente,
    pp.datas_fim_pausa AS fim_pendencia_cliente,
    pp.total_dias_pausado AS sla_pendencia_cliente,
    pp.num_ciclos AS num_ciclos_pausa,
    pp.detalhamento_periodos AS detalhamento_pausas,

    -- MÉTRICAS DE SLA
    CASE
        WHEN r.requested_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN (DATE(p.opened_at) - DATE(r.requested_at))::INTEGER
        ELSE NULL
    END AS sla_recrutamento,

    v.sla_days_goal AS prazo_processo_seletivo,

    CASE
        WHEN COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) >= DATE(p.opened_at)
             AND (usp.data_ultima_mudanca IS NOT NULL OR p.hired_at IS NOT NULL)
        THEN (COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at)) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER
        ELSE NULL
    END AS sla_geral,

    CASE
        WHEN v.sla_days_goal IS NOT NULL
            AND p.hired_at IS NOT NULL
            AND DATE(p.hired_at) >= DATE(p.opened_at)
        THEN
            CASE
                WHEN (DATE(p.hired_at) - DATE(p.opened_at))::INTEGER <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,

    -- PESSOA CONTRATADA
    p.reason AS motivo_contratacao,
    pct.talent_name AS nome_pessoa_contratada,
    pct.talent_email AS email_pessoal,

    -- ORIGEM DO CANDIDATO
    sp.source AS source_candidato,
    CASE
        WHEN sp.source IN ('referral', 'direct-referral', 'employee') THEN TRUE
        ELSE FALSE
    END AS is_referral

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
    LEFT JOIN source_posicao sp ON sp.posicao_id = p.id
    LEFT JOIN ultimo_status_posicao usp ON usp.posicao_id = p.id
    LEFT JOIN motivo_cancelamento_pausa mcp ON mcp.posicao_id = p.id  -- ✅ NOVO

WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')

ORDER BY p.opened_at DESC NULLS LAST;

-- COMENTÁRIO
COMMENT ON VIEW vw_analise_posicoes IS
'View para análise de posições - Migration 045 (Quick Fix - 2026-03-20)
CORREÇÃO CRÍTICA: Motivo de cancelamento agora vem de position_timeline.notes.';

COMMENT ON COLUMN vw_analise_posicoes.motivo_cancelamento_paralisacao IS
'Motivo do cancelamento ou paralisação. Vem de position_timeline.notes. CORRIGIDO na migration 045.';
