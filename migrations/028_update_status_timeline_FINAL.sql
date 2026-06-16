/*
================================================================================
MIGRATION 028: Atualiza Status via Timeline (VERSÃO FINAL)
================================================================================

Data: 2026-02-06
Descrição:
  Atualiza view vw_analise_posicoes com melhorias:
  1. status_atual - buscar último new_status da position_timeline
  2. data_encerramento_ou_atualizacao - buscar último changed_at da position_timeline
  3. FILTRAR vagas tipo "Banco de Talentos"

  CAMPOS DE CANDIDATO NA VIEW (mantidos apenas esses 2):
  - nome_pessoa_contratada
  - email_pessoal

  FILTROS APLICADOS:
  - Excluir vaga_id: 114, 99, 479, 88, 680
  - Excluir Tipo: "Banco de Talentos"

Impacto:
  - View passa de 831 para 830 colunas (remove 1 posição de Banco de Talentos)
  - status_atual agora vem de position_timeline (mais preciso)
  - data_encerramento_ou_atualizacao vem de position_timeline (mais preciso)

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view com melhorias e filtro de Banco de Talentos
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
eventos_pausa AS (
    SELECT DISTINCT
        posicao_id,
        changed_at,
        previous_status,
        new_status,
        CASE
            WHEN previous_status = 'open' AND new_status = 'paused' THEN 'INICIO_PAUSA'
            WHEN previous_status = 'paused' AND new_status IN ('open', 'canceled', 'closed') THEN 'FIM_PAUSA'
            ELSE 'OUTRO'
        END AS tipo_evento
    FROM position_timeline
    WHERE (previous_status = 'open' AND new_status = 'paused')
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
            -- Prioriza source do candidato contratado
            (SELECT cd.source
             FROM candidaturas cd
             WHERE cd.vaga_id = p.vaga_id
             AND cd.stage_name = 'Contratação'
             LIMIT 1),
            -- Fallback: source mais comum
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
    p.id AS id_position,
    v.name AS cargo,
    DATE(r.requested_at) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,
    v.sla_days_goal AS prazo_processo_seletivo,
    c.name AS cliente,
    r.custom_fields->>'Torre' AS torre,
    COALESCE(usp.new_status, p.status) AS status_atual,
    COALESCE(DATE(usp.data_ultima_mudanca), DATE(p.hired_at), CURRENT_DATE) AS data_encerramento_ou_atualizacao,
    v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao,
    ue.stage_name AS etapa_funil,
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,
    p.reason AS motivo_contratacao,
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,
    COALESCE(v.custom_fields->>'Gestor', r.user_name) AS responsavel,
    v.user_name AS recrutador_vaga,
    pp.datas_inicio_pausa AS inicio_pendencia_cliente,
    pp.datas_fim_pausa AS fim_pendencia_cliente,
    pp.total_dias_pausado AS sla_pendencia_cliente,
    pp.num_ciclos AS num_ciclos_pausa,
    pp.detalhamento_periodos AS detalhamento_pausas,
    CASE
        WHEN r.requested_at IS NOT NULL AND p.opened_at IS NOT NULL
        THEN (DATE(p.opened_at) - DATE(r.requested_at))::INTEGER
        ELSE NULL
    END AS sla_recrutamento,
    pct.talent_name AS nome_pessoa_contratada,
    pct.talent_email AS email_pessoal,
    v.custom_fields->>'Modalidade de Contratação' AS modalidade_contratacao,
    (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at)))::INTEGER AS sla_geral,
    CASE
        WHEN v.sla_days_goal IS NOT NULL THEN
            CASE
                WHEN (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at))) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo,
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
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
    AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')
ORDER BY p.opened_at DESC NULLS LAST;

-- Comentário na view
COMMENT ON VIEW vw_analise_posicoes IS 'View analítica de posições com métricas de performance, SLA, pendências e origem. Atualizada em 2026-02-06 com status via timeline. Exclui vagas com IDs específicos e tipo Banco de Talentos (29 colunas).';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_num_cols INTEGER;
    v_banco_talentos INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;
    SELECT COUNT(*) INTO v_num_cols
    FROM information_schema.columns
    WHERE table_name = 'vw_analise_posicoes';

    -- Verificar se ainda tem Banco de Talentos
    SELECT COUNT(*) INTO v_banco_talentos
    FROM vw_analise_posicoes vap
    INNER JOIN posicoes p ON p.id = vap.id_position
    INNER JOIN vagas v ON v.id = p.vaga_id
    WHERE v.custom_fields->>'Tipo' = 'Banco de Talentos';

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VALIDAÇÃO DA MIGRATION 028 (VERSÃO FINAL)';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: % (esperado: 830)', v_total;
    RAISE NOTICE 'Total de colunas: %', v_num_cols;
    RAISE NOTICE 'Banco de Talentos na view: % (esperado: 0)', v_banco_talentos;
    RAISE NOTICE '';
    RAISE NOTICE 'Melhorias aplicadas:';
    RAISE NOTICE '  1. status_atual agora vem de position_timeline';
    RAISE NOTICE '  2. data_encerramento_ou_atualizacao vem de position_timeline';
    RAISE NOTICE '  3. Filtro adicionado: Banco de Talentos excluído';
    RAISE NOTICE '';
    RAISE NOTICE 'Filtros ativos:';
    RAISE NOTICE '  - Exclui vaga_id: 114, 99, 479, 88, 680';
    RAISE NOTICE '  - Exclui Tipo: "Banco de Talentos"';
    RAISE NOTICE '================================================================================';
END $$;

/*
================================================================================
ESTRUTURA FINAL DA VIEW (29 colunas)
================================================================================
Filtros aplicados:
- WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
- AND (v.custom_fields->>'Tipo' IS NULL OR v.custom_fields->>'Tipo' != 'Banco de Talentos')

Total esperado: 830 posições (831 - 1 Banco de Talentos)
================================================================================
*/
