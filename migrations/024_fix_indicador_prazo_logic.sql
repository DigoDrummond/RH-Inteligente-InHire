/*
================================================================================
MIGRATION 024: Correção da Lógica do Campo indicador_prazo
================================================================================

Data: 2026-02-06
Descrição:
  Corrige o campo indicador_prazo para preencher todas as posições,
  retornando "Sem Meta Definida" quando sla_days_goal for NULL,
  ao invés de deixar o campo NULL.

Problema:
  - 193 posições (23.2%) tinham sla_geral calculado mas indicador_prazo NULL
  - Causa: lógica só calculava quando sla_days_goal não era NULL

Solução:
  - Quando sla_days_goal é NULL, retorna "Sem Meta Definida"
  - Agora 100% das posições têm indicador_prazo preenchido

Impacto:
  - 193 posições que estavam com indicador_prazo NULL agora mostram "Sem Meta Definida"
  - Não afeta posições que já tinham meta definida

================================================================================
*/

-- Remove view existente
DROP VIEW IF EXISTS vw_analise_posicoes CASCADE;

-- Recria view com lógica corrigida
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
        t.name AS talent_name,
        t.email AS talent_email,
        ROW_NUMBER() OVER (PARTITION BY cd.vaga_id ORDER BY cd.updated_at_inhire DESC) AS rn
    FROM candidaturas cd
    INNER JOIN talentos t ON t.inhire_id = cd.talent_inhire_id
    WHERE cd.stage_name = 'Contratação' AND cd.stage_order > 9
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
        -- Usa CURRENT_TIMESTAMP se não houver fim (posição ainda pausada)
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
)
SELECT
    p.id AS id_position,
    v.name AS cargo,
    DATE(r.requested_at) AS data_abertura,
    DATE(p.opened_at) AS data_publicacao,
    v.sla_days_goal AS prazo_processo_seletivo,
    c.name AS cliente,
    r.custom_fields->>'Torre' AS torre,
    p.status AS status_atual,
    COALESCE(DATE(p.hired_at), CURRENT_DATE) AS data_encerramento_ou_atualizacao,
    v.custom_fields->>'Motivo de Cancelamento' AS motivo_cancelamento_paralisacao,
    ue.stage_name AS etapa_funil,
    COALESCE(v.custom_fields->>'Senioridade', v.seniority::text) AS senioridade,
    p.reason AS motivo_contratacao,
    v.custom_fields->>'Se substituição, informar o nome do colaborador: ' AS pessoa_substituida,
    r.user_name AS responsavel,
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
    v.custom_fields->>'Classificação' AS classificacao_vaga,
    v.area AS area_vaga,

    /*
    ============================================================================
    CAMPO CORRIGIDO: indicador_prazo
    ============================================================================
    ANTES: Retornava NULL quando sla_days_goal era NULL
    AGORA: Retorna "Sem Meta Definida" quando sla_days_goal é NULL

    Valores possíveis:
    - "Dentro do Prazo": quando SLA <= meta
    - "Fora do Prazo": quando SLA > meta
    - "Sem Meta Definida": quando não há meta (sla_days_goal NULL)
    ============================================================================
    */
    CASE
        WHEN v.sla_days_goal IS NOT NULL THEN
            CASE
                WHEN (COALESCE(DATE(p.hired_at), CURRENT_DATE) - DATE(COALESCE(r.requested_at, p.opened_at))) <= v.sla_days_goal
                THEN 'Dentro do Prazo'
                ELSE 'Fora do Prazo'
            END
        ELSE 'Sem Meta Definida'
    END AS indicador_prazo

FROM posicoes p
    INNER JOIN vagas v ON p.vaga_id = v.id
    LEFT JOIN requisicoes r ON r.job_inhire_id = v.inhire_id
    LEFT JOIN clientes c ON c.inhire_id = v.tenant_client_id
    LEFT JOIN ultima_etapa ue ON ue.vaga_id = p.vaga_id AND ue.rn = 1
    LEFT JOIN pessoa_contratada pct ON pct.vaga_id = p.vaga_id AND pct.rn = 1
    LEFT JOIN pendencias_posicao pp ON pp.posicao_id = p.id
WHERE p.vaga_id NOT IN (114, 99, 479, 88, 680)
ORDER BY p.opened_at DESC NULLS LAST;

-- Comentário na view
COMMENT ON VIEW vw_analise_posicoes IS 'View analítica de posições com métricas de performance, SLA e pendências. Atualizada em 2026-02-06 com correção no campo indicador_prazo.';

-- Validação
DO $$
DECLARE
    v_total INTEGER;
    v_com_indicador INTEGER;
    v_sem_meta INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM vw_analise_posicoes;
    SELECT COUNT(*) INTO v_com_indicador FROM vw_analise_posicoes WHERE indicador_prazo IS NOT NULL;
    SELECT COUNT(*) INTO v_sem_meta FROM vw_analise_posicoes WHERE indicador_prazo = 'Sem Meta Definida';

    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'VALIDAÇÃO DA MIGRATION 024';
    RAISE NOTICE '================================================================================';
    RAISE NOTICE 'Total de posições: %', v_total;
    RAISE NOTICE 'Posições com indicador_prazo: % (%.1f%%)', v_com_indicador, (v_com_indicador::NUMERIC / v_total * 100);
    RAISE NOTICE 'Posições "Sem Meta Definida": % (%.1f%%)', v_sem_meta, (v_sem_meta::NUMERIC / v_total * 100);

    IF v_com_indicador = v_total THEN
        RAISE NOTICE '✓ SUCESSO: Todas as posições têm indicador_prazo preenchido';
    ELSE
        RAISE EXCEPTION '✗ ERRO: % posições sem indicador_prazo', (v_total - v_com_indicador);
    END IF;

    RAISE NOTICE '================================================================================';
END $$;

/*
================================================================================
RESULTADO ESPERADO:
================================================================================
Total de posições: 831
Posições com indicador_prazo: 831 (100.0%)
Posições "Sem Meta Definida": 193 (23.2%)
✓ SUCESSO: Todas as posições têm indicador_prazo preenchido
================================================================================
*/
